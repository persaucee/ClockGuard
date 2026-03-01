import uuid
from typing import List

from app.models.User import Employee
from app.schemas import APIResponse, EmployeeCreate, EmployeeResponse, EmployeeUpdate, VerifyRequest
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

@router.post("/", response_model=APIResponse[EmployeeResponse])
async def add_employee(
    employee: EmployeeCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    
    employee_record = Employee(**employee.model_dump())
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
    db: AsyncSession = Depends(get_db)
):
    input_vector = request.embedding

    #Postgres statement to calculate cosine similarity and return the most similar employee
    stmt = (
        select(
            Employee,
            (1 - (Employee.embedding.cosine_distance(input_vector))).label("similarity")
        )
        .order_by(Employee.embedding.cosine_distance(input_vector))
        .limit(1)
    )

    result = await db.execute(stmt)
    row = result.first()
    employee, similarity = row

    if not employee or similarity < 0.85:
        raise HTTPException(status_code=404, detail="No matching employee found")

    return {
        "match": {"name": employee.name},
        "similarity": float(similarity),
        "verified": similarity > 0.85
    } 