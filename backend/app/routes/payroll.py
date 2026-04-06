from collections import defaultdict
from datetime import date
import uuid
from typing import List, Optional
from fastapi.responses import JSONResponse
from app.models.User import Employee, PayrollSession
from app.schemas import APIResponse, PayrollSessionCreate, PayrollSessionResponse
from app.utils import send_payroll_email, create_response
from dependencies import get_current_user, get_db
from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks

router = APIRouter(prefix="/payroll")

@router.get("/report", response_model=APIResponse)
async def get_payroll_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    processed: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
) -> JSONResponse:
    if (start_date is not None and end_date is not None and start_date > end_date):
        return create_response(
            success=False,
            message="Invalid date range",
            status_code=400
        )
    query_filters = [
        Employee.organization_id == current_user.organization_id,
    ]
    if start_date is not None:
        query_filters.append(PayrollSession.shift_date >= start_date)
    if end_date is not None:
        query_filters.append(PayrollSession.shift_date <= end_date)
    if processed is not None:
        query_filters.append(PayrollSession.processed == processed)
    
    result = await db.execute(
        select(
            Employee.id.label("employee_id"),
            Employee.name.label("employee_name"),
            Employee.email.label("employee_email"),
            Employee.hourly_rate.label("hourly_rate"),
            func.sum(PayrollSession.total_hours).label("total_hours"),
            func.sum(PayrollSession.total_pay).label("total_pay"),
            func.sum(PayrollSession.tip_amount).label("total_tips"),
            func.count(PayrollSession.id).label("session_count"),
        )
        .join(PayrollSession, PayrollSession.employee_id == Employee.id)
        .where(*query_filters)
        .group_by(Employee.id, Employee.name, Employee.email, Employee.hourly_rate)
        .order_by(Employee.name)
    )

    rows = result.all()

    report_data = [
        {
            "employee_id": str(row.employee_id),
            "employee_name": row.employee_name,
            "employee_email": row.employee_email,
            "hourly_rate": row.hourly_rate,
            "total_hours": round(row.total_hours or 0, 2),
            "total_pay": round(row.total_pay or 0, 2),
            "total_tips": round(row.total_tips or 0, 2),
            "session_count": row.session_count,
        }
        for row in rows
    ]
    return create_response(
        success=True,
        data=report_data,
        message="Payroll report retrieved successfully",
        status_code=200
    )

@router.post("/process", response_model=APIResponse)
async def process_payroll(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    payroll_ids: Optional[List[uuid.UUID]] = Body(default=None),
) -> JSONResponse:

    if (start_date is None) != (end_date is None):
        return create_response(
            success=False,
            status_code=422,
            message="start date and end date must both be provided together."
        )
    if start_date and end_date and start_date > end_date:
        return create_response(
            success=False,
            status_code=422,
            message="start date must be before or equal to end date."
        )

    emp_result = await db.execute(
        select(Employee).where(
            Employee.organization_id == current_user.organization_id
        )
    )
    employees = emp_result.scalars().all()
    session_filter = [
        PayrollSession.employee_id.in_([e.id for e in employees]),
        PayrollSession.processed == False,
    ]

    if payroll_ids:
        session_filter.append(PayrollSession.id.in_(payroll_ids))
    elif start_date and end_date:
        session_filter.append(PayrollSession.shift_date >= start_date)
        session_filter.append(PayrollSession.shift_date <= end_date)

    session_result = await db.execute(select(PayrollSession).with_for_update().where(*session_filter))
    sessions_by_employee = defaultdict(list)
    for s in session_result.scalars().all():
        sessions_by_employee[s.employee_id].append(s)

    tasks_queued = 0
    pending_emails = []

    for employee in employees:
        if employee.hourly_rate is None or not employee.email:
            continue
        sessions = sessions_by_employee.get(employee.id, [])
        total_hours = sum(s.total_hours or 0 for s in sessions)
        total_tips = sum(s.tip_amount or 0 for s in sessions)
        if total_hours == 0 and total_tips == 0:
            continue
        if not employee.hourly_rate or not employee.email:
            continue
        total_pay = (total_hours * employee.hourly_rate) + total_tips
        pending_emails.append((employee.email, total_pay, total_hours))
        for session in sessions:
            session.processed = True

        tasks_queued += 1

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    for email, total_pay, total_hours in pending_emails:
        background_tasks.add_task(send_payroll_email, email, total_pay, total_hours)

    return create_response(
        success=True,
        message=f"Payroll processing initiated for {tasks_queued} employee(s)."
    )

#TODO: debug endpoint, will remove in prod
@router.post("/email/{employee_id}", response_model=APIResponse)
async def send_email(
    employee_id: uuid.UUID,
    total_pay: float,
    total_hours: float,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
) -> JSONResponse:
    employee = await db.execute(select(Employee).where(Employee.id == employee_id, Employee.organization_id == current_user.organization_id))
    employee = employee.scalar_one_or_none()
    if not employee:
        return create_response(
            success=False,
            message="Employee not found",
            status_code=404
        )
    background_tasks.add_task(send_payroll_email, employee.email, total_pay, total_hours)
    return create_response(
        success=True,
        message="Payroll email sent successfully"
    )

@router.get("/{employee_id}", response_model=APIResponse[List[PayrollSessionResponse]])
async def get_employee_payroll_sessions(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
) -> JSONResponse:
    result = await db.execute(
        select(PayrollSession)
        .join(PayrollSession.employee)
        .where(
            PayrollSession.employee_id == employee_id,
            Employee.organization_id == current_user.organization_id
        )
    )
    sessions = result.scalars().all()
    sessions_response = [
        PayrollSessionResponse.model_validate(s)
        for s in sessions
    ]
    return create_response(
        success=True,
        data=sessions_response,
        message="Payroll sessions retrieved successfully"
    )

@router.put("/{session_id}", response_model=APIResponse[PayrollSessionResponse])
async def edit_payroll_session(
    session_id: uuid.UUID,
    record: PayrollSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
) -> JSONResponse:
    payroll_session = await db.execute(
        select(PayrollSession)
        .join(PayrollSession.employee)
        .where(
            PayrollSession.id == session_id,
            Employee.organization_id == current_user.organization_id
        )
    )
    payroll_session = payroll_session.scalar_one_or_none()
    if not payroll_session:
        return create_response(
            success=False,
            message="Payroll session not found",
            status_code=404
        )
    payroll_session.shift_date = record.shift_date
    payroll_session.tip_amount = record.tip_amount
    payroll_session.total_hours = record.total_hours
    payroll_session.total_pay = record.total_pay
    await db.commit()
    await db.refresh(payroll_session)
    return create_response(
        success=True,
        data=PayrollSessionResponse.model_validate(payroll_session),
        message="Payroll session updated successfully"
    )
