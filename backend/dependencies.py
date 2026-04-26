import os

from app.database import AsyncSessionLocal
from app.models.User import Admin
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

LOGIN_SECRET = os.getenv("LOGIN_SECRET")

async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


def get_token_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return token

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Admin:
    token = get_token_from_cookie(request)
    try:
        payload = jwt.decode(token, LOGIN_SECRET, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials (Invalid or Expired Token)")
    
    result = await db.execute(select(Admin).filter(Admin.username == username))
    user = result.scalars().first()
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user