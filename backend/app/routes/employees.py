import uuid
from typing import List
import datetime

from fastapi.responses import JSONResponse

from app.models.User import AttendanceLog, Employee, PayrollSession
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

SIMILARITY_THRESHOLD = 0.7

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
        return JSONResponse(
            status_code=404,
            content=APIResponse(
                success=False,
                message="Employee not found"
            ).model_dump()
        )

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
        return JSONResponse(
            status_code=404,
            content=APIResponse(
                success=False,
                message="No matching employee found"
            ).model_dump()
        )
    employee, similarity = row

    if not employee or similarity < SIMILARITY_THRESHOLD:
        return JSONResponse(
            status_code=404,
            content=APIResponse(
                success=False,
                message="No matching employee found"
            ).model_dump()
        )

    # Determine IN/OUT from last log
    last_log_result = await db.execute(
        select(AttendanceLog)
        .where(AttendanceLog.employee_id == employee.id)
        .order_by(AttendanceLog.timestamp.desc())
        .limit(1)
    )
    last_log = last_log_result.scalars().first()

    action = "OUT" if (last_log and last_log.action == "IN") else "IN"
    attendance_log = AttendanceLog(
        employee_id=employee.id,
        action=action
    )
    db.add(attendance_log)
    await db.flush()

    payroll_session = None

    if action == "OUT":
        clock_in_result = await db.execute(
            select(AttendanceLog)
            .where(
                AttendanceLog.employee_id == employee.id,
                AttendanceLog.action == "IN",
            )
            .order_by(AttendanceLog.timestamp.desc())
            .limit(1)
        )
        clock_in_log = clock_in_result.scalars().first()

        if clock_in_log:
            clock_in_time = clock_in_log.timestamp
            clock_out_time = attendance_log.timestamp

            # Fallback: if DB hasn't populated the timestamp yet, use now()
            if clock_out_time is None:
                from datetime import timezone
                clock_out_time = datetime.now(tz=timezone.utc)

            duration_seconds = (clock_out_time - clock_in_time).total_seconds()
            total_hours = duration_seconds / 3600
            hourly_rate = employee.hourly_rate or 0.0
            total_pay = total_hours * hourly_rate
            
            payroll_session = PayrollSession(
                employee_id=employee.id,
                shift_date=clock_in_time.date(),
                clock_in_time=clock_in_time,
                clock_out_time=clock_out_time,
                total_hours=round(total_hours, 4),
                total_pay=round(total_pay, 2),
            )
            db.add(payroll_session)

    await db.commit()

    response_data = {
        "match": {"employee_id": str(employee.id),
                  "name": employee.name},
        "similarity": float(similarity),
        "verified": similarity > SIMILARITY_THRESHOLD,
        "action": action,
    }
    if payroll_session:
        response_data["payroll_session"] = {
            "shift_date": str(payroll_session.shift_date),
            "clock_in_time": str(payroll_session.clock_in_time),
            "clock_out_time": str(payroll_session.clock_out_time),
            "total_hours": payroll_session.total_hours,
            "total_pay": payroll_session.total_pay,
        }

    return response_data
