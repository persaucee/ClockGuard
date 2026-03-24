import uuid
from typing import List

from app.models.User import AttendanceLog, Employee
from app.schemas import (
    APIResponse,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    VerifyRequest,
)
from dependencies import get_current_user, get_db
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()
router = APIRouter(prefix="/employees")

# Endpoints
@router.get("/", response_model=APIResponse[List[EmployeeResponse]])
async def get_employees(current_user: dict = Depends(get_current_user), 
                        db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Employee).where(
            Employee.organization_id == current_user.organization_id
        )
    )
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
    result = await db.execute(
        select(Employee).where(
            Employee.id == employee_id,
            Employee.organization_id == current_user.organization_id
        )
    )
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

@router.post("/", response_model=APIResponse[EmployeeResponse])
async def add_employee(
    employee: EmployeeCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    
    employee_data = employee.model_dump()
    employee_data["organization_id"] = current_user.organization_id
    employee_record = Employee(**employee_data)
    db.add(employee_record)
    await db.commit()
    await db.refresh(employee_record)

    return APIResponse(
        success=True,
        data=employee_record,
        message="Employee added successfully"
    )

@router.post("/verify")
async def verify(
    request: VerifyRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    input_vector = request.embedding

    #Postgres statement to calculate cosine similarity and return the most similar employee
    stmt = (
        select(
            Employee,
            (1 - (Employee.embedding.cosine_distance(input_vector))).label("similarity")
        )
        .where(Employee.organization_id == current_user.organization_id)
        .order_by(Employee.embedding.cosine_distance(input_vector))
        .limit(1)
    )

    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="No matching employee found")
    employee, similarity = row

    if not employee or similarity < 0.80:
        raise HTTPException(status_code=404, detail="No matching employee found")
    elif request.action not in ["IN", "OUT"]:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'IN' or 'OUT'.")
    
    attendance_log = AttendanceLog(
    employee_id=employee.id,
    action=request.action
)
    db.add(attendance_log)
    await db.commit()

    return {
        "match": {"employee_id": str(employee.id)},
        "similarity": float(similarity),
        "verified": similarity > 0.80
    } 