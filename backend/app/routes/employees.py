from app.schemas import APIResponse, EmployeeResponse
from dotenv import load_dotenv
from fastapi import APIRouter
from typing import List

from app.models.User import Employee
from app.schemas import APIResponse
from dependencies import get_current_user, get_db
from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()
router = APIRouter(prefix="/employees")

# Endpoints
@router.get("/", response_model=APIResponse[List[EmployeeResponse]])
async def get_employees(current_user: dict = Depends(get_current_user), 
                        db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee))
    return APIResponse(
        success=True,
        data=result.scalars().all(),
        message="Employees retrieved successfully")