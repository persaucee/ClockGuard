"""
Hourly background job that auto-clocks-out employees who are still
logged in after their organization's default_close_time has passed.
"""

import logging, os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.User import AttendanceLog, Employee, Organization, PayrollSession

logger = logging.getLogger(__name__)
load_dotenv()
JOB_INTERVAL_MINUTES = int(os.getenv("CRON_INTERVAL_MINUTES", 60))

async def auto_close_shifts() -> None:
    """
    Runs every JOB_INTERVAL_MINUTES minutes, starting at 00:00.

    Steps
    -----
    1. Find every organization whose default_close_time falls within the
       past JOB_INTERVAL_MINUTES window  (i.e.  now-interval  <  close_time  <=  now).
    2. For each matched org, find employees whose *last* attendance log
       is an 'IN' — meaning they are still clocked in.
    3. Synthesise an 'OUT' AttendanceLog hardcoded to close_time.
    4. Calculate total_hours / total_pay and write a PayrollSession
       with requires_admin_review = True.
    """
    now_utc = datetime.now(tz=timezone.utc)

    logger.info(
        "[Scheduler] auto_close_shifts fired at %s UTC (interval: %d min)",
        now_utc.isoformat(),
        JOB_INTERVAL_MINUTES,
    )

    async with AsyncSessionLocal() as db:
        try:
            await _process_close_outs(db, now_utc)
            await db.commit()
            logger.info("[Scheduler] auto_close_shifts completed successfully")
        except Exception:
            await db.rollback()
            logger.exception("[Scheduler] auto_close_shifts failed — rolled back")


async def _process_close_outs(
    db: AsyncSession,
    now_utc: datetime,
) -> None:
    eastern_offset = timedelta(hours=-4)
    now_eastern = (now_utc + eastern_offset).time().replace(second=0, microsecond=0)

    org_result = await db.execute(
        select(Organization).where(
            Organization.default_close_time.isnot(None),
            Organization.default_close_time <= now_eastern,
        )
    )
    organizations = org_result.scalars().all()

    if not organizations:
        logger.info("[Scheduler] No organizations hit close_time in this window.")
        return

    logger.info("[Scheduler] %d organization(s) matched close_time window.", len(organizations))

    for org in organizations:
        await _auto_close_org(db, org, now_utc)


async def _auto_close_org(
    db: AsyncSession,
    org: Organization,
    now_utc: datetime,
) -> None:
    from sqlalchemy import func as sqlfunc

    latest_ts_subq = (
        select(
            AttendanceLog.employee_id,
            sqlfunc.max(AttendanceLog.timestamp).label("latest_ts"),
        )
        .join(Employee, Employee.id == AttendanceLog.employee_id)
        .where(Employee.organization_id == org.id)
        .group_by(AttendanceLog.employee_id)
        .subquery()
    )

    still_in_result = await db.execute(
        select(AttendanceLog, Employee)
        .join(Employee, Employee.id == AttendanceLog.employee_id)
        .join(
            latest_ts_subq,
            (latest_ts_subq.c.employee_id == AttendanceLog.employee_id)
            & (latest_ts_subq.c.latest_ts == AttendanceLog.timestamp),
        )
        .where(
            Employee.organization_id == org.id,
            AttendanceLog.action == "IN",
        )
    )
    rows = still_in_result.all()

    if not rows:
        logger.info("[Scheduler] Org %s — no employees still clocked IN.", org.id)
        return

    logger.info(
        "[Scheduler] Org %s — %d employee(s) still clocked IN, generating auto-OUT.",
        org.id,
        len(rows),
    )

    eastern_offset = timedelta(hours=-4)
    now_eastern = now_utc + eastern_offset
    close_dt = datetime.combine(now_eastern.date(), org.default_close_time) - eastern_offset
    close_dt = close_dt.replace(tzinfo=timezone.utc)

    for log_in, employee in rows:
        await _create_auto_out(db, employee, log_in, close_dt, now_utc)


async def _create_auto_out(
    db: AsyncSession,
    employee: Employee,
    log_in: AttendanceLog,
    close_dt: datetime,
    now_utc: datetime,
) -> None:
    effective_close_dt = now_utc if close_dt <= log_in.timestamp else close_dt

    auto_out_log = AttendanceLog(
        employee_id=employee.id,
        action="OUT",
        timestamp=effective_close_dt,
    )
    db.add(auto_out_log)

    duration_seconds = (effective_close_dt - log_in.timestamp).total_seconds()
    total_hours = round(duration_seconds / 3600, 4)
    hourly_rate = employee.hourly_rate or 0.0
    total_pay = round(total_hours * hourly_rate, 2)

    payroll_session = PayrollSession(
        employee_id=employee.id,
        shift_date=log_in.timestamp.date(),
        clock_in_time=log_in.timestamp,
        clock_out_time=effective_close_dt,
        total_hours=total_hours,
        total_pay=total_pay,
        requires_admin_review=True,
    )
    db.add(payroll_session)

    logger.info(
        "[Scheduler] Employee %s | IN: %s | OUT: %s | %.4fh | £%.2f | flagged for review",
        employee.id,
        log_in.timestamp.isoformat(),
        effective_close_dt.isoformat(),
        total_hours,
        total_pay,
    )

_scheduler = AsyncIOScheduler()


def start_scheduler(interval_minutes: int = JOB_INTERVAL_MINUTES) -> None:
    """
    Parameters
    ----------
    interval_minutes:
        How often the job runs, in minutes.  Must divide 60 evenly if you
        want clean on-the-hour alignment (e.g. 60, 30, 15, 10, 5).
    """
    _scheduler.add_job(
        auto_close_shifts,
        trigger=IntervalTrigger(
            minutes=interval_minutes,
            start_date=_next_aligned_start(interval_minutes),
        ),
        id="auto_close_shifts",
        replace_existing=True,
        misfire_grace_time=300,  # allow up to 5 min late if server was briefly down
    )
    _scheduler.start()
    logger.info(
        "[Scheduler] APScheduler started — auto_close_shifts registered "
        "(interval: every %d min, aligned to 00:00 UTC)",
        interval_minutes,
    )


def stop_scheduler() -> None:
    _scheduler.shutdown(wait=False)
    logger.info("[Scheduler] APScheduler stopped.")


def _next_aligned_start(interval_minutes: int) -> datetime:
    """
    Return the next UTC datetime that is aligned to the given interval,
    anchored at midnight (00:00 UTC).
    """
    now = datetime.now(tz=timezone.utc)
    minutes_since_midnight = now.hour * 60 + now.minute
    intervals_elapsed = minutes_since_midnight // interval_minutes
    next_boundary_minutes = (intervals_elapsed + 1) * interval_minutes
    next_start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        minutes=next_boundary_minutes
    )
    return next_start