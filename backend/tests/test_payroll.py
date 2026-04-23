import pytest
import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.routes import payroll as payroll_mod


# ---------------------------------------------------------------------------
# Fake DB helpers
# ---------------------------------------------------------------------------

class FakeResult:
    def __init__(self, scalar_value=None, scalars_list=None, rows=None,
                 scalar_one_or_none_value=None):
        self._scalar = scalar_value
        self._scalars = scalars_list or []
        self._rows = rows or []
        self._scalar_one_or_none = scalar_one_or_none_value

    def scalar(self):
        return self._scalar

    def scalar_one_or_none(self):
        return self._scalar_one_or_none

    def scalars(self):
        return FakeScalars(self._scalars)

    def all(self):
        return self._rows


class FakeScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


def make_db(*results):
    results = list(results)
    call_count = {"n": 0}

    async def execute(q):
        idx = call_count["n"]
        call_count["n"] += 1
        return results[idx]

    async def commit(): pass
    async def rollback(): pass
    async def refresh(obj): pass

    return SimpleNamespace(
        execute=execute,
        commit=commit,
        rollback=rollback,
        refresh=refresh,
    )


# ---------------------------------------------------------------------------
# Dummy models
# ---------------------------------------------------------------------------

class DummyEmployee:
    def __init__(self, id=None, organization_id=None, hourly_rate=20.0,
                 email="emp@test.com", name="Test Employee"):
        self.id = id or uuid.uuid4()
        self.organization_id = organization_id or uuid.uuid4()
        self.name = name
        self.hourly_rate = hourly_rate
        self.email = email


class DummyPayrollSession:
    def __init__(self, id=None, employee_id=None, employee=None,
                 shift_date=None, total_hours=8.0, total_pay=160.0,
                 tip_amount=None, processed=False):
        self.id = id or uuid.uuid4()
        self.employee_id = employee_id or uuid.uuid4()
        self.employee = employee
        self.shift_date = shift_date or date.today()
        self.clock_in_time = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        self.clock_out_time = datetime(2024, 1, 1, 17, 0, 0, tzinfo=timezone.utc)
        self.total_hours = total_hours
        self.total_pay = total_pay
        self.tip_amount = tip_amount
        self.processed = processed
        self.requires_admin_review = False


class DummyPayrollSessionCreate:
    def __init__(self):
        self.shift_date = date(2024, 1, 1)
        self.clock_in_time = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        self.clock_out_time = datetime(2024, 1, 1, 17, 0, 0, tzinfo=timezone.utc)
        self.tip_amount = 10.0

    def model_dump(self, exclude_unset=False):
        return {
            "shift_date": self.shift_date,
            "clock_in_time": self.clock_in_time,
            "clock_out_time": self.clock_out_time,
            "tip_amount": self.tip_amount,
        }


class DummyBackgroundTasks:
    def __init__(self):
        self.tasks = []

    def add_task(self, func, *args, **kwargs):
        self.tasks.append((func, args, kwargs))


# ---------------------------------------------------------------------------
# GET /payroll/report tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_payroll_report_success(monkeypatch):
    monkeypatch.setattr(
        payroll_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    org_id = uuid.uuid4()
    current_user = SimpleNamespace(organization_id=org_id)

    # Fake row with named attributes matching the SELECT labels
    row = SimpleNamespace(
        employee_id=uuid.uuid4(),
        employee_name="Test Employee",
        employee_email="emp@test.com",
        hourly_rate=20.0,
        total_hours=8.0,
        total_pay=160.0,
        total_tips=5.0,
        session_count=1,
    )

    db = make_db(
        FakeResult(scalar_value=1),   # count query
        FakeResult(rows=[row]),        # report rows
    )

    res = await payroll_mod.get_payroll_report(
        start_date=None,
        end_date=None,
        processed=None,
        page=1,
        page_size=50,
        db=db,
        current_user=current_user,
    )

    assert res.success is True
    assert len(res.data) == 1
    assert res.data[0]["employee_name"] == "Test Employee"
    assert res.data[0]["total_hours"] == 8.0
    assert res.meta["total_items"] == 1


@pytest.mark.asyncio
async def test_get_payroll_report_invalid_date_range(monkeypatch):
    monkeypatch.setattr(
        payroll_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    db = make_db()
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await payroll_mod.get_payroll_report(
        start_date=date(2024, 2, 1),
        end_date=date(2024, 1, 1),   # end before start
        processed=None,
        page=1,
        page_size=50,
        db=db,
        current_user=current_user,
    )

    assert res.success is False
    assert "Invalid date range" in res.message


@pytest.mark.asyncio
async def test_get_payroll_report_empty(monkeypatch):
    monkeypatch.setattr(
        payroll_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    db = make_db(
        FakeResult(scalar_value=0),
        FakeResult(rows=[]),
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await payroll_mod.get_payroll_report(
        start_date=None,
        end_date=None,
        processed=None,
        page=1,
        page_size=50,
        db=db,
        current_user=current_user,
    )

    assert res.success is True
    assert res.data == []
    assert res.meta["total_items"] == 0


# ---------------------------------------------------------------------------
# POST /payroll/process tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_payroll_success(monkeypatch):
    monkeypatch.setattr(
        payroll_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )
    monkeypatch.setattr(payroll_mod, "send_payroll_email", lambda *a, **kw: None)

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id, hourly_rate=20.0, email="emp@test.com")
    session = DummyPayrollSession(employee_id=emp.id, total_hours=8.0, processed=False)

    db = make_db(
        FakeResult(scalars_list=[emp]),      # employees query
        FakeResult(scalars_list=[session]),  # sessions query
    )
    current_user = SimpleNamespace(organization_id=org_id)
    background_tasks = DummyBackgroundTasks()

    res = await payroll_mod.process_payroll(
        background_tasks=background_tasks,
        db=db,
        current_user=current_user,
        start_date=None,
        end_date=None,
        payroll_ids=None,
    )

    assert res.success is True
    assert "1 employee" in res.message
    assert session.processed is True
    # Email task should be queued
    assert len(background_tasks.tasks) == 1
    assert background_tasks.tasks[0][1][0] == "emp@test.com"


@pytest.mark.asyncio
async def test_process_payroll_only_one_date_provided(monkeypatch):
    """Providing only start_date without end_date returns validation error."""
    monkeypatch.setattr(
        payroll_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    db = make_db()
    current_user = SimpleNamespace(organization_id=uuid.uuid4())
    background_tasks = DummyBackgroundTasks()

    res = await payroll_mod.process_payroll(
        background_tasks=background_tasks,
        db=db,
        current_user=current_user,
        start_date=date(2024, 1, 1),
        end_date=None,
        payroll_ids=None,
    )

    assert res.success is False
    assert "both" in res.message.lower()


@pytest.mark.asyncio
async def test_process_payroll_invalid_date_range(monkeypatch):
    monkeypatch.setattr(
        payroll_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    db = make_db()
    current_user = SimpleNamespace(organization_id=uuid.uuid4())
    background_tasks = DummyBackgroundTasks()

    res = await payroll_mod.process_payroll(
        background_tasks=background_tasks,
        db=db,
        current_user=current_user,
        start_date=date(2024, 2, 1),
        end_date=date(2024, 1, 1),
        payroll_ids=None,
    )

    assert res.success is False
    assert "before or equal" in res.message


@pytest.mark.asyncio
async def test_process_payroll_skips_employees_without_hours(monkeypatch):
    """Employees with zero hours and zero tips are skipped."""
    monkeypatch.setattr(
        payroll_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )
    monkeypatch.setattr(payroll_mod, "send_payroll_email", lambda *a, **kw: None)

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id)

    # Session has 0 hours and no tips — should be skipped
    session = DummyPayrollSession(employee_id=emp.id, total_hours=0, total_pay=0)

    db = make_db(
        FakeResult(scalars_list=[emp]),
        FakeResult(scalars_list=[session]),
    )
    current_user = SimpleNamespace(organization_id=org_id)
    background_tasks = DummyBackgroundTasks()

    res = await payroll_mod.process_payroll(
        background_tasks=background_tasks,
        db=db,
        current_user=current_user,
        start_date=None,
        end_date=None,
        payroll_ids=None,
    )

    assert res.success is True
    assert "0 employee" in res.message
    assert len(background_tasks.tasks) == 0


# ---------------------------------------------------------------------------
# GET /payroll/ tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_all_payroll_sessions(monkeypatch):
    monkeypatch.setattr(
        payroll_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )
    monkeypatch.setattr(
        payroll_mod.PayrollSessionResponse, "model_validate",
        lambda s: SimpleNamespace(id=s.id, employee_id=s.employee_id)
    )

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id)
    s1 = DummyPayrollSession(employee_id=emp.id)
    s2 = DummyPayrollSession(employee_id=emp.id)

    db = make_db(
        FakeResult(scalar_value=2),
        FakeResult(scalars_list=[s1, s2]),
    )
    current_user = SimpleNamespace(organization_id=org_id)

    res = await payroll_mod.get_all_payroll_sessions(
        db=db,
        current_user=current_user,
        page=1,
        page_size=50,
    )

    assert res.success is True
    # Sessions are grouped by employee — one employee = one group
    assert len(res.data) == 1
    assert len(res.data[0]) == 2
    assert res.meta["total_items"] == 2


@pytest.mark.asyncio
async def test_get_all_payroll_sessions_multiple_employees(monkeypatch):
    """Sessions from different employees end up in separate groups."""
    monkeypatch.setattr(
        payroll_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )
    monkeypatch.setattr(
        payroll_mod.PayrollSessionResponse, "model_validate",
        lambda s: SimpleNamespace(id=s.id, employee_id=s.employee_id)
    )

    org_id = uuid.uuid4()
    emp1 = DummyEmployee(organization_id=org_id)
    emp2 = DummyEmployee(organization_id=org_id)
    s1 = DummyPayrollSession(employee_id=emp1.id)
    s2 = DummyPayrollSession(employee_id=emp2.id)

    db = make_db(
        FakeResult(scalar_value=2),
        FakeResult(scalars_list=[s1, s2]),
    )
    current_user = SimpleNamespace(organization_id=org_id)

    res = await payroll_mod.get_all_payroll_sessions(
        db=db,
        current_user=current_user,
        page=1,
        page_size=50,
    )

    assert res.success is True
    assert len(res.data) == 2  # two separate employee groups


# ---------------------------------------------------------------------------
# GET /payroll/{employee_id} tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_employee_payroll_sessions(monkeypatch):
    monkeypatch.setattr(
        payroll_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )
    monkeypatch.setattr(
        payroll_mod.PayrollSessionResponse, "model_validate",
        lambda s: SimpleNamespace(id=s.id, employee_id=s.employee_id)
    )

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id)
    s1 = DummyPayrollSession(employee_id=emp.id)

    db = make_db(
        FakeResult(scalar_value=1),
        FakeResult(scalars_list=[s1]),
    )
    current_user = SimpleNamespace(organization_id=org_id)

    res = await payroll_mod.get_employee_payroll_sessions(
        employee_id=emp.id,
        db=db,
        current_user=current_user,
        page=1,
        page_size=50,
    )

    assert res.success is True
    assert len(res.data) == 1
    assert res.meta["total_items"] == 1


# ---------------------------------------------------------------------------
# PUT /payroll/{session_id} tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_edit_payroll_session_success(monkeypatch):
    monkeypatch.setattr(
        payroll_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )
    monkeypatch.setattr(
        payroll_mod.PayrollSessionResponse, "model_validate",
        lambda s: SimpleNamespace(id=s.id, total_hours=s.total_hours, total_pay=s.total_pay)
    )

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id, hourly_rate=20.0)
    session = DummyPayrollSession(employee_id=emp.id, employee=emp)

    db = make_db(FakeResult(scalar_one_or_none_value=session))
    current_user = SimpleNamespace(organization_id=org_id)
    record = DummyPayrollSessionCreate()

    res = await payroll_mod.edit_payroll_session(
        session_id=session.id,
        record=record,
        db=db,
        current_user=current_user,
    )

    assert res.success is True
    # 9am -> 5pm = 8 hours * $20/hr + $10 tip = $170
    assert session.total_hours == 8.0
    assert session.total_pay == 170.0


@pytest.mark.asyncio
async def test_edit_payroll_session_not_found(monkeypatch):
    monkeypatch.setattr(
        payroll_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    db = make_db(FakeResult(scalar_one_or_none_value=None))
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await payroll_mod.edit_payroll_session(
        session_id=uuid.uuid4(),
        record=DummyPayrollSessionCreate(),
        db=db,
        current_user=current_user,
    )

    assert res.success is False
    assert "not found" in res.message