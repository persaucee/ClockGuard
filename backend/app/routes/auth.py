import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.User import Admin
from app.schemas import APIResponse, LoginData, UserData
from app.utils import create_response
from dependencies import get_current_user, get_db
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, status
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