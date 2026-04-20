import uuid
from typing import List
from datetime import datetime, timezone

from app.models.User import AttendanceLog, Employee, PayrollSession
from app.schemas import (
    APIResponse,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    VerifyRequest,
)
from app.utils import create_response
from dependencies import get_current_user, get_db
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.websockets.ws_router import org_ws_manager

load_dotenv()
router = APIRouter(prefix="/employees")

SIMILARITY_THRESHOLD = 0.7
EMBEDDING_DIM = 512

# Endpoints
@router.get("/", response_model=APIResponse[List[EmployeeResponse]])
async def get_employees(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    filters = (Employee.organization_id == current_user.organization_id,)

    count_q = select(func.count()).select_from(Employee).where(*filters)
    total_res = await db.execute(count_q)
    total_items = int(total_res.scalar() or 0)

    total_pages = (total_items + page_size - 1) // page_size if page_size else 0
    offset = (page - 1) * page_size

    result = await db.execute(
        select(Employee)
        .where(*filters)
        .order_by(Employee.id)
        .limit(page_size)
        .offset(offset)
    )

    items = result.scalars().all()

    final_data = [EmployeeResponse.model_validate(r) for r in items]

    meta = {"page": page, "page_size": page_size, "total_items": total_items, "total_pages": total_pages}

    return create_response(success=True, data=final_data, message="Employees retrieved successfully", meta=meta)

@router.post("/", response_model=APIResponse[EmployeeResponse])
async def add_employee(
    employee: EmployeeCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
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

    except SQLAlchemyError:
        await db.rollback()
        return APIResponse(
            success=False,
            data=None,
            message="Failed to add employee"
        )

@router.post("/verify")
async def verify(
    request: VerifyRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    input_vector = request.embedding
    if len(input_vector) != EMBEDDING_DIM:
        return create_response(
            success=False,
            message=f"Invalid embedding vector length, expected {EMBEDDING_DIM}, but got {len(input_vector)}",
            status_code=400
        )

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
        return create_response(
            success=False,
            message="No matching employee found",
            status_code=404
        )
    employee, similarity = row

    if not employee or similarity < SIMILARITY_THRESHOLD:
        return create_response(
            success=False,
            message="No matching employee found",
            status_code=404
        )

    # Determine IN/OUT from last log
    last_log_result = await db.execute(
        select(AttendanceLog)
        .where(AttendanceLog.employee_id == employee.id)
        .order_by(AttendanceLog.timestamp.desc())
        .limit(1)
        .with_for_update()
    )
    last_log = last_log_result.scalars().first()
    
    action = "OUT" if (last_log and last_log.action == "IN") else "IN"
    try:
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
    except SQLAlchemyError:
        await db.rollback()
        return APIResponse(
            success=False,
            data=None,
            message="Failed to verify employee, try again later"
        )

    response_data = {
        "match": {
            "employee_id": str(employee.id),
            "name": employee.name,
            "email": employee.email,
        },
        "similarity": float(similarity),
        "verified": similarity >= SIMILARITY_THRESHOLD,
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
    await org_ws_manager.broadcast_to_org(
        current_user.organization_id,
        {
            "event": "clock_event",
            **response_data,
        }
    )

    return create_response(
        success=True,
        data=response_data,
        message="Employee verified successfully"
    )

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
        return create_response(
            success=False,
            message="Employee not found",
            status_code=404
        )

    try:
        update_data = employee.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(employee_record, field, value)

        await db.commit()
        await db.refresh(employee_record)
    except SQLAlchemyError:
        await db.rollback()
        return create_response(
            success=False,
            message="Failed to update employee on our end, try again later",
            status_code=500
        )

    return APIResponse(
        success=True,
        data=employee_record,
        message="Employee updated successfully"
    )
