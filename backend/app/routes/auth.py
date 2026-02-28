import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.models.User import Admin
from app.schemas import APIResponse, LoginData, UserData
from dependencies import get_current_user, get_db
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()
router = APIRouter(prefix="/auth")

# Configuration
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
LOGIN_SECRET = os.getenv("LOGIN_SECRET")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = data.copy()
    to_encode.update({"exp": expire, "sub": data.get("sub")})
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username and/or password"
        )
    
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    response = APIResponse(
        success=True,
        message="Logged in successfully"
    )
    json_response = JSONResponse(response.model_dump())
    json_response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return json_response

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return APIResponse(
        success=True, 
        data=UserData(username=current_user.username, first_name=current_user.first_name, last_name=current_user.last_name),
        message="User info retrieved")