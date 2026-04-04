import uuid
from typing import List

from datetime import date, datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.orm import joinedload
from app.models.User import PayrollSession, Employee, AttendanceLog
from app.schemas import (
    APIResponse,
    AttendanceRecordResponse,
    EmployeeResponse,
    ClockStatusData,
)
from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy import func, and_
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


@router.get("/status", response_model=APIResponse[ClockStatusData])
async def get_attendance_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    emp_result = await db.execute(select(Employee).where(Employee.organization_id == current_user.organization_id))
    employees = emp_result.scalars().all()

    # latest timestamp per employee within the organization
    last_ts_subq = (
        select(
            AttendanceLog.employee_id,
            func.max(AttendanceLog.timestamp).label("last_ts"),
        )
        .join(Employee, AttendanceLog.employee_id == Employee.id)
        .where(Employee.organization_id == current_user.organization_id)
        .group_by(AttendanceLog.employee_id)
        .subquery()
    )

    # Join back to attendance_logs to get the last action per employee
    last_logs_q = (
        select(AttendanceLog.employee_id, AttendanceLog.action, AttendanceLog.timestamp)
        .join(last_ts_subq, and_(AttendanceLog.employee_id == last_ts_subq.c.employee_id, AttendanceLog.timestamp == last_ts_subq.c.last_ts))
    )

    res = await db.execute(last_logs_q)
    rows = res.all()

    last_map: dict = {r[0]: {"action": r[1], "timestamp": r[2]} for r in rows}

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    currently_clocked_in: list[Employee] = []
    inactive_24h: list[Employee] = []

    for emp in employees:
        last = last_map.get(emp.id)
        if last and last.get("action") == "IN":
            currently_clocked_in.append(emp)
        if (not last) or (last.get("timestamp") is None) or (last.get("timestamp") < cutoff):
            inactive_24h.append(emp)

    def to_employee_response(e: Employee) -> EmployeeResponse:
        return EmployeeResponse(
            id=e.id,
            name=e.name,
            hourly_rate=e.hourly_rate,
            email=e.email,
            organization_id=e.organization_id,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )

    data = ClockStatusData(
        clocked_in=[to_employee_response(e) for e in currently_clocked_in],
        inactive=[to_employee_response(e) for e in inactive_24h],
    )

    return APIResponse(success=True, data=data, message="Attendance status retrieved successfully")