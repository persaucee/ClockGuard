from datetime import date
import uuid
from fastapi.responses import JSONResponse
from app.models.User import Employee, PayrollSession
from app.utils import send_payroll_email
from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/payroll")


@router.post("/email/{employee_id}")
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
        return JSONResponse(status_code=404, content={"success": False, "message": "Employee not found"})
    send_payroll_email(employee.email,total_pay,total_hours)
    return JSONResponse(content={"success": True, "message": "Payroll email sent successfully"})


@router.get("/report")
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

    return JSONResponse(content=[
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
    ])