from datetime import date
import uuid
from typing import List
from fastapi.responses import JSONResponse
from app.models.User import Employee, PayrollSession
from app.schemas import APIResponse, PayrollSessionCreate, PayrollSessionResponse
from app.utils import send_payroll_email, create_response
from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/payroll")

#TODO: update endpoint to fetch info from records instead of request body.
@router.post("/email/{employee_id}", response_model=APIResponse)
async def send_email(
    employee_id: uuid.UUID,
    total_pay: float,
    total_hours: float,
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
    send_payroll_email(employee.email, total_pay, total_hours)
    return create_response(
        success=True,
        message="Payroll email sent successfully"
    )

@router.get("/", response_model=APIResponse[List[PayrollSessionResponse]])
async def get_payroll_sessions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
) -> JSONResponse:
    result = await db.execute(
        select(PayrollSession).where(PayrollSession.employee_id == current_user.id)
    )
    sessions = result.scalars().all()
    return create_response(
        success=True,
        data=sessions,
        message="Payroll sessions retrieved successfully"
    )

@router.post("/{id}", response_model=APIResponse[PayrollSessionResponse])
async def edit_payroll_session(
    record: PayrollSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
) -> JSONResponse:
    payroll_session = await db.execute(
        select(PayrollSession)
        .join(PayrollSession.employee)
        .where(
            PayrollSession.id == id,
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
    payroll_session = PayrollSession(
        employee_id=record.employee_id,
        shift_date=record.shift_date,
        tip_amount=record.tip_amount,
        total_hours=record.total_hours,
        total_pay=record.total_pay
    )
    db.add(payroll_session)
    await db.commit()
    await db.refresh(payroll_session)
    return create_response(
        success=True,
        data=payroll_session,
        message="Payroll session updated successfully"
    )

@router.get("/report", response_model=APIResponse)
async def get_payroll_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
) -> JSONResponse:
    result = await db.execute(
        select(
            Employee.id.label("employee_id"),
            Employee.name.label("employee_name"),
            Employee.email.label("employee_email"),
            Employee.hourly_rate.label("hourly_rate"),
            func.sum(PayrollSession.total_hours).label("total_hours"),
            func.sum(PayrollSession.total_pay).label("total_pay"),
            func.count(PayrollSession.id).label("session_count"),
        )
        .join(PayrollSession, PayrollSession.employee_id == Employee.id)
        .where(
            Employee.organization_id == current_user.organization_id,
            PayrollSession.shift_date >= start_date,
            PayrollSession.shift_date <= end_date,
        )
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
            "total_hours": round(row.total_hours, 2),
            "total_pay": round(row.total_pay, 2),
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