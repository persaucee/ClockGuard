from typing import List
import uuid

from app.models.User import Employee
from app.schemas import APIResponse, EmployeeResponse, EmployeeUpdate
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

@router.put("/{employee_id}", response_model=APIResponse[EmployeeResponse])
async def edit_employee(
    employee_id: uuid.UUID,
    employee: EmployeeUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Employee).filter(Employee.id == employee_id))
    employee_record = result.scalars().first()

    if employee_record is None:
        return APIResponse(success=False, message="Employee not found")

    update_data = employee.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(employee_record, field, value)

    await db.commit()
    await db.refresh(employee_record)

    return APIResponse(
        success=True,
        data=employee_record,
        message="Employee updated successfully"
    )