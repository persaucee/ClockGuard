import uuid
from typing import List

from datetime import date
from typing import Optional, List
from sqlalchemy.orm import joinedload
from app.models.User import PayrollSession, Employee
from app.schemas import (
    APIResponse,
    AttendanceRecordResponse
)
from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/attendance")

@router.get("/logs", response_model=APIResponse[List[AttendanceRecordResponse]])
async def get_attendance_records(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(PayrollSession)
        .join(PayrollSession.employee)
        .options(joinedload(PayrollSession.employee))
        .where(Employee.organization_id == current_user.organization_id)
    )

    if start_date:
        query = query.where(PayrollSession.shift_date >= start_date)
    if end_date:
        query = query.where(PayrollSession.shift_date <= end_date)

    query = query.order_by(PayrollSession.shift_date.desc())

    result = await db.execute(query)
    records = result.scalars().unique().all()

    data = [
        AttendanceRecordResponse(
            id=r.id,
            employee_name=r.employee.name,
            clock_in_time=r.clock_in_time,
            clock_out_time=r.clock_out_time,
            total_hours=r.total_hours,
        )
        for r in records
    ]

    return APIResponse(success=True, data=data, message="Attendance records retrieved successfully")

@router.get("/logs/{employee_id}", response_model=APIResponse[List[AttendanceRecordResponse]])
async def get_employee_attendance_records(
    employee_id: uuid.UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(PayrollSession)
        .join(PayrollSession.employee)
        .options(joinedload(PayrollSession.employee))
        .where(
            Employee.organization_id == current_user.organization_id,
            PayrollSession.employee_id == employee_id,
        )
    )

    if start_date:
        query = query.where(PayrollSession.shift_date >= start_date)
    if end_date:
        query = query.where(PayrollSession.shift_date <= end_date)

    query = query.order_by(PayrollSession.shift_date.desc())

    result = await db.execute(query)
    records = result.scalars().unique().all()

    data = [
        AttendanceRecordResponse(
            id=r.id,
            employee_name=r.employee.name,
            clock_in_time=r.clock_in_time,
            clock_out_time=r.clock_out_time,
            total_hours=r.total_hours,
        )
        for r in records
    ]

    return APIResponse(success=True, data=data, message="Attendance records retrieved successfully")