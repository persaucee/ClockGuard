import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.User import Admin, Organization

from app.schemas import (
    APIResponse,
    LoginData,
    UserData,
    LoginResponseData,
    Verify2FARequest,
    TwoFactorSetupResponse,
    TwoFactorCodeRequest,
    RegisterDataRequest, 
    RegisterDataResponse,
)

from app.utils import create_response

from app.security.two_factor import (
    create_temp_2fa_token,
    decode_temp_2fa_token,
    generate_totp_secret,
    get_totp_uri,
    verify_totp_code,
)

from dependencies import get_current_user, get_db
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()
router = APIRouter(prefix="/auth")

# Configuration
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
LOGIN_SECRET = os.getenv("LOGIN_SECRET")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = data.copy()
    to_encode.update({"exp": expire, "sub": data.get("sub"), "type": "access"})
    encoded_jwt = jwt.encode(to_encode, LOGIN_SECRET, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode = data.copy()
    to_encode.update({"exp": expire, "sub": data.get("sub"), "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, LOGIN_SECRET, algorithm="HS256")
    return encoded_jwt


@router.post("/register")
async def register(
    form_data: RegisterDataRequest,
    db: AsyncSession = Depends(get_db)
):
    username = form_data.username.lower()

    existing_user = await db.execute(
        select(Admin).filter(Admin.username == username)
    )
    if existing_user.scalars().first():
        return create_response(
            success=False,
            message="Username already exists",
            status_code=400
        )
    hashed_password = await run_in_threadpool(
        pwd_context.hash,
        form_data.password
    )
    new_org = Organization(
        name=form_data.organization_name,
        default_open_time=form_data.open_time,
        default_close_time=form_data.close_time
    )
    db.add(new_org)
    await db.flush()
    new_admin = Admin(
        username=username,
        password_hash=hashed_password,
        first_name=form_data.first_name,
        last_name=form_data.last_name,
        organization_id=new_org.id
    )
    db.add(new_admin)
    try:
        await db.commit()
    except:
        await db.rollback()
        raise
    await db.refresh(new_org)
    await db.refresh(new_admin)
    access_token = create_access_token(
        data={"sub": new_admin.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(
        data={"sub": new_admin.username}
    )

    response_body = create_response(
        success=True,
        data=RegisterDataResponse(
            username=new_admin.username,
            first_name=new_admin.first_name,
            last_name=new_admin.last_name,
            organization_id=new_org.id,
            organization_name=new_org.name,
            open_time=new_org.default_open_time,
            close_time=new_org.default_close_time
        ),
        message="User registered successfully"
    )
    # TODO: set secure=true in production
    json_response = JSONResponse(content=jsonable_encoder(response_body))
    json_response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    json_response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return json_response

# Endpoints
@router.post("/login")
async def login(form_data: LoginData, 
                db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Admin).filter(Admin.username == form_data.username.lower()))
    user = result.scalars().first()
    
    is_valid = False
    if user:
        is_valid = await run_in_threadpool(verify_password, form_data.password, user.password_hash)

    if not user or not is_valid:
        return create_response(
            success=False,
            message="Incorrect username and/or password",
            status_code=401
        )

    if user.two_factor_enabled:
        temp_token = create_temp_2fa_token(user.username)
        response = APIResponse(
            success=True,
            data=LoginResponseData(
                two_factor_required=True,
                temp_token=temp_token
            ),
            message="Two-factor authentication required"
        )
        return JSONResponse(content=jsonable_encoder(response))
        
    
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username}
    )
    response = APIResponse(
        success=True,
        data=LoginResponseData(
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            organization_id=user.organization_id,
            two_factor_required=False
        ),
        message="Logged in successfully"
    )
    json_response = JSONResponse(content=jsonable_encoder(response))
    json_response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False, #TODO: Set to true in production
        samesite="strict",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    json_response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # TODO: Set to true in production
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return json_response


@router.post("/verify-2fa")
async def verify_2fa(
    request_data: Verify2FARequest,
    db: AsyncSession = Depends(get_db)
):
    username = decode_temp_2fa_token(request_data.temp_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired temporary token"
        )

    result = await db.execute(
        select(Admin).filter(Admin.username == username)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.two_factor_enabled or not user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled for this account"
        )

    valid_code = verify_totp_code(user.two_factor_secret, request_data.code)
    if not valid_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication code"
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username}
    )

    response = APIResponse(
        success=True,
        data=UserData(
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            organization_id=user.organization_id
        ),
        message="Logged in successfully"
    )

    json_response = JSONResponse(content=jsonable_encoder(response))
    json_response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    json_response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return json_response


@router.post("/refresh")
async def refresh_token_endpoint(request: Request):

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token missing"
        )
    try:
        payload = jwt.decode(refresh_token, LOGIN_SECRET, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token")
        username = payload.get("sub")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    new_access_token = create_access_token(
        data={"sub": username}
    )
    response = JSONResponse({
        "success": True,
        "message": "Token refreshed"
    })
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,  # TODO: True in production
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return response

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return create_response(
        success=True, 
        data=UserData(
            username=current_user.username, 
            first_name=current_user.first_name, 
            last_name=current_user.last_name, 
            organization_id=current_user.organization_id
        ),
        message="User info retrieved"
    )

@router.post("/2fa/setup/initiate")
async def initiate_2fa_setup(
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    secret = generate_totp_secret()
    current_user.two_factor_secret = secret
    current_user.two_factor_enabled = False

    await db.commit()
    await db.refresh(current_user)

    return APIResponse(
        success=True,
        data=TwoFactorSetupResponse(
            secret=secret,
            otpauth_url=get_totp_uri(secret, current_user.username)
        ),
        message="Two-factor setup initiated"
    )


@router.post("/2fa/setup/confirm")
async def confirm_2fa_setup(
    request_data: TwoFactorCodeRequest,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor setup has not been initiated"
        )

    valid_code = verify_totp_code(current_user.two_factor_secret, request_data.code)
    if not valid_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication code"
        )

    current_user.two_factor_enabled = True
    await db.commit()
    await db.refresh(current_user)

    return APIResponse(
        success=True,
        message="Two-factor authentication enabled successfully"
    )

@router.post("/2fa/disable")
async def disable_2fa(
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None

    await db.commit()
    await db.refresh(current_user)

    return APIResponse(
        success=True,
        message="Two-factor authentication disabled successfully"
    )