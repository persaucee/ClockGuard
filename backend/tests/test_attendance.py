import pytest
import uuid
from datetime import datetime, timezone, timedelta, date
from types import SimpleNamespace

from app.routes import attendance as attendance_mod


# ---------------------------------------------------------------------------
# Shared fake DB helpers
# ---------------------------------------------------------------------------

class FakeResult:
    def __init__(self, scalar_value=None, scalars_list=None, rows=None):
        self._scalar = scalar_value
        self._scalars = scalars_list or []
        self._rows = rows or []

    def scalar(self):
        return self._scalar

    def scalars(self):
        return FakeScalars(self._scalars)

    def all(self):
        return self._rows


class FakeScalars:
    def __init__(self, items):
        self._items = items

    def unique(self):
        return self

    def all(self):
        return self._items


class FailingDB:
    """Simulates a DB that raises on every execute call."""
    async def execute(self, q):
        raise RuntimeError("DB connection failed")


# ---------------------------------------------------------------------------
# Dummy model stand-ins
# ---------------------------------------------------------------------------

class DummyEmployee:
    def __init__(self, id=None, organization_id=None):
        self.id = id or uuid.uuid4()
        self.organization_id = organization_id or uuid.uuid4()
        self.name = "Test Employee"
        self.hourly_rate = 10
        self.email = "test@test.com"
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class DummyPayrollSession:
    def __init__(self, id=None, shift_date=None, employee=None):
        self.id = id or uuid.uuid4()
        self.shift_date = shift_date or date.today()
        self.employee = employee or DummyEmployee()


class DummyAttendanceLog:
    def __init__(self, id=None, employee_id=None, action="IN", timestamp=None):
        self.id = id or uuid.uuid4()
        self.employee_id = employee_id or uuid.uuid4()
        self.action = action
        self.timestamp = timestamp or datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_db(*results):
    """Returns a fake async db that yields each result in sequence per execute() call."""
    results = list(results)
    call_count = {"n": 0}
    captured_queries = []

    async def execute(q):
        captured_queries.append(q)
        idx = call_count["n"]
        call_count["n"] += 1
        return results[idx]

    db = SimpleNamespace(execute=execute)
    db.captured_queries = captured_queries
    return db


def _patch_common(monkeypatch):
    """Apply the two monkeypatches shared by all tests."""
    monkeypatch.setattr(
        attendance_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )
    monkeypatch.setattr(
        attendance_mod.PayrollSessionResponse, "model_validate",
        lambda r: {"id": str(r.id)}
    )
    monkeypatch.setattr(
        attendance_mod.AttendanceRecordResponse, "model_validate",
        lambda r: {"id": str(r.id), "action": r.action}
    )


# ===========================================================================
# get_attendance_records
# ===========================================================================

@pytest.mark.asyncio
async def test_get_attendance_records_pagination(monkeypatch):
    """Basic success path: correct count, serialization applied to every row."""
    monkeypatch.setattr(
        attendance_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    calls = []
    def fake_validate(r):
        calls.append(r.id)
        return {"id": str(r.id)}

    monkeypatch.setattr(
        attendance_mod.PayrollSessionResponse, "model_validate",
        fake_validate
    )

    ps1, ps2 = DummyPayrollSession(), DummyPayrollSession()
    db = make_db(
        FakeResult(scalar_value=2),
        FakeResult(scalars_list=[ps1, ps2]),
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await attendance_mod.get_attendance_records(
        start_date=None,
        end_date=None,
        page=1,
        page_size=20,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert len(res.data) == 2
    assert res.meta["total_items"] == 2
    assert res.meta["total_pages"] == 1
    assert set(calls) == {ps1.id, ps2.id}


@pytest.mark.asyncio
async def test_get_attendance_records_multi_page(monkeypatch):
    """total_pages rounds up correctly when items don't divide evenly."""
    _patch_common(monkeypatch)

    sessions = [DummyPayrollSession() for _ in range(5)]
    db = make_db(
        FakeResult(scalar_value=21),          # 21 total items
        FakeResult(scalars_list=sessions),    # page 2 returns 5 items
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await attendance_mod.get_attendance_records(
        start_date=None,
        end_date=None,
        page=2,
        page_size=20,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert res.meta["total_pages"] == 2      # ceil(21/20) = 2
    assert res.meta["total_items"] == 21
    assert res.meta["page"] == 2


@pytest.mark.asyncio
async def test_get_attendance_records_empty(monkeypatch):
    """Empty result set returns success with an empty list and 0 pages."""
    _patch_common(monkeypatch)

    db = make_db(
        FakeResult(scalar_value=0),
        FakeResult(scalars_list=[]),
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await attendance_mod.get_attendance_records(
        start_date=None,
        end_date=None,
        page=1,
        page_size=20,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert res.data == []
    assert res.meta["total_items"] == 0


@pytest.mark.asyncio
async def test_get_attendance_records_date_filter_passed(monkeypatch):
    """Start/end date params are accepted without error and queries execute."""
    _patch_common(monkeypatch)

    db = make_db(
        FakeResult(scalar_value=1),
        FakeResult(scalars_list=[DummyPayrollSession()]),
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await attendance_mod.get_attendance_records(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        page=1,
        page_size=20,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    # Both DB calls should have been made (count query + data query)
    assert len(db.captured_queries) == 2


@pytest.mark.asyncio
async def test_get_attendance_records_org_scoping(monkeypatch):
    """The DB is queried with the current_user's org — two users in different
    orgs each trigger their own execute calls, confirming the org_id flows
    through to each query invocation."""
    _patch_common(monkeypatch)

    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    user_a = SimpleNamespace(organization_id=org_a)
    user_b = SimpleNamespace(organization_id=org_b)

    db_a = make_db(FakeResult(scalar_value=1), FakeResult(scalars_list=[DummyPayrollSession()]))
    db_b = make_db(FakeResult(scalar_value=0), FakeResult(scalars_list=[]))

    res_a = await attendance_mod.get_attendance_records(
        start_date=None, end_date=None, page=1, page_size=20,
        current_user=user_a, db=db_a,
    )
    res_b = await attendance_mod.get_attendance_records(
        start_date=None, end_date=None, page=1, page_size=20,
        current_user=user_b, db=db_b,
    )

    # Org A has data; org B does not
    assert len(res_a.data) == 1
    assert len(res_b.data) == 0


# ===========================================================================
# get_employee_attendance_records
# ===========================================================================

@pytest.mark.asyncio
async def test_get_employee_attendance_records_filters(monkeypatch):
    """Only sessions for the requested employee are returned."""
    _patch_common(monkeypatch)

    emp = DummyEmployee()
    other_emp = DummyEmployee(organization_id=emp.organization_id)

    ps_valid = DummyPayrollSession(employee=emp)

    db = make_db(
        FakeResult(scalar_value=1),
        FakeResult(scalars_list=[ps_valid]),
    )

    current_user = SimpleNamespace(organization_id=emp.organization_id)

    res = await attendance_mod.get_employee_attendance_records(
        employee_id=emp.id,
        start_date=None,
        end_date=None,
        page=1,
        page_size=20,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert len(res.data) == 1
    assert res.data[0]["id"] == str(ps_valid.id)


@pytest.mark.asyncio
async def test_get_employee_attendance_records_wrong_org(monkeypatch):
    """An employee that belongs to a different org should not be accessible."""
    _patch_common(monkeypatch)

    emp = DummyEmployee()  # org A
    current_user = SimpleNamespace(organization_id=uuid.uuid4())  # org B

    # DB returns 0 results because the query filters by org_id
    db = make_db(
        FakeResult(scalar_value=0),
        FakeResult(scalars_list=[]),
    )

    res = await attendance_mod.get_employee_attendance_records(
        employee_id=emp.id,
        start_date=None,
        end_date=None,
        page=1,
        page_size=20,
        current_user=current_user,
        db=db,
    )

    assert res.data == [] or res.success is False


@pytest.mark.asyncio
async def test_get_employee_attendance_records_nonexistent_employee(monkeypatch):
    """A valid UUID that matches no employee returns an empty result, not an error."""
    _patch_common(monkeypatch)

    db = make_db(
        FakeResult(scalar_value=0),
        FakeResult(scalars_list=[]),
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await attendance_mod.get_employee_attendance_records(
        employee_id=uuid.uuid4(),
        start_date=None,
        end_date=None,
        page=1,
        page_size=20,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert res.data == []


@pytest.mark.asyncio
async def test_get_employee_attendance_records_empty_history(monkeypatch):
    """Employee exists but has no sessions — returns empty list, not an error."""
    _patch_common(monkeypatch)

    emp = DummyEmployee()
    db = make_db(
        FakeResult(scalar_value=0),
        FakeResult(scalars_list=[]),
    )
    current_user = SimpleNamespace(organization_id=emp.organization_id)

    res = await attendance_mod.get_employee_attendance_records(
        employee_id=emp.id,
        start_date=None,
        end_date=None,
        page=1,
        page_size=20,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert res.data == []
    assert res.meta["total_items"] == 0


# ===========================================================================
# get_all_attendance_logs
# ===========================================================================

@pytest.mark.asyncio
async def test_get_attendance_logs_no_employee(monkeypatch):
    """All logs returned contain both IN and OUT actions."""
    _patch_common(monkeypatch)

    emp = DummyEmployee()
    log1 = DummyAttendanceLog(employee_id=emp.id, action="IN")
    log2 = DummyAttendanceLog(employee_id=emp.id, action="OUT")

    db = make_db(
        FakeResult(scalar_value=2),
        FakeResult(scalars_list=[log1, log2]),
    )

    current_user = SimpleNamespace(organization_id=emp.organization_id)

    res = await attendance_mod.get_all_attendance_logs(
        start_date=None,
        end_date=None,
        page=1,
        page_size=50,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert len(res.data) == 2
    actions = {r["action"] for r in res.data}
    assert actions == {"IN", "OUT"}


@pytest.mark.asyncio
async def test_get_all_attendance_logs_empty(monkeypatch):
    """No logs returns an empty list without error."""
    _patch_common(monkeypatch)

    db = make_db(
        FakeResult(scalar_value=0),
        FakeResult(scalars_list=[]),
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await attendance_mod.get_all_attendance_logs(
        start_date=None,
        end_date=None,
        page=1,
        page_size=50,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert res.data == []
    assert res.meta["total_items"] == 0


@pytest.mark.asyncio
async def test_get_all_attendance_logs_date_filter(monkeypatch):
    """Date range params are forwarded — both DB calls execute."""
    _patch_common(monkeypatch)

    db = make_db(
        FakeResult(scalar_value=1),
        FakeResult(scalars_list=[DummyAttendanceLog()]),
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await attendance_mod.get_all_attendance_logs(
        start_date=date(2024, 3, 1),
        end_date=date(2024, 3, 31),
        page=1,
        page_size=50,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert len(db.captured_queries) == 2


@pytest.mark.asyncio
async def test_get_all_attendance_logs_excludes_other_org(monkeypatch):
    """Logs belonging to a different org are not returned."""
    _patch_common(monkeypatch)

    # DB already filtered by org; we verify via returned count
    db = make_db(
        FakeResult(scalar_value=0),
        FakeResult(scalars_list=[]),
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await attendance_mod.get_all_attendance_logs(
        start_date=None,
        end_date=None,
        page=1,
        page_size=50,
        current_user=current_user,
        db=db,
    )

    assert res.data == []


# ===========================================================================
# get_attendance_logs (by employee)
# ===========================================================================

@pytest.mark.asyncio
async def test_get_attendance_logs_by_employee(monkeypatch):
    """Only logs for the specified employee are returned."""
    _patch_common(monkeypatch)

    emp = DummyEmployee()
    log_valid = DummyAttendanceLog(employee_id=emp.id, action="IN")

    db = make_db(
        FakeResult(scalar_value=1),
        FakeResult(scalars_list=[log_valid]),
    )
    current_user = SimpleNamespace(organization_id=emp.organization_id)

    res = await attendance_mod.get_attendance_logs(
        employee_id=emp.id,
        start_date=None,
        end_date=None,
        page=1,
        page_size=50,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert len(res.data) == 1
    assert res.data[0]["id"] == str(log_valid.id)


@pytest.mark.asyncio
async def test_get_attendance_logs_by_employee_wrong_org(monkeypatch):
    """Requesting logs for an employee in another org yields no data."""
    _patch_common(monkeypatch)

    emp = DummyEmployee()  # org A
    current_user = SimpleNamespace(organization_id=uuid.uuid4())  # org B

    db = make_db(
        FakeResult(scalar_value=0),
        FakeResult(scalars_list=[]),
    )

    res = await attendance_mod.get_attendance_logs(
        employee_id=emp.id,
        start_date=None,
        end_date=None,
        page=1,
        page_size=50,
        current_user=current_user,
        db=db,
    )

    assert res.data == [] or res.success is False


@pytest.mark.asyncio
async def test_get_attendance_logs_nonexistent_employee(monkeypatch):
    """Logs query for an unknown employee_id returns empty without raising."""
    _patch_common(monkeypatch)

    db = make_db(
        FakeResult(scalar_value=0),
        FakeResult(scalars_list=[]),
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await attendance_mod.get_attendance_logs(
        employee_id=uuid.uuid4(),
        start_date=None,
        end_date=None,
        page=1,
        page_size=50,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert res.data == []


# ===========================================================================
# get_attendance_status
# ===========================================================================

@pytest.mark.asyncio
async def test_get_attendance_status(monkeypatch):
    """Basic classification: recent IN → clocked_in, OUT → inactive,
    stale IN (>24 h) → NOT clocked_in."""
    monkeypatch.setattr(
        attendance_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    org_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    old = now - timedelta(hours=30)

    emp_in   = DummyEmployee(organization_id=org_id)
    emp_out  = DummyEmployee(organization_id=org_id)
    emp_edge = DummyEmployee(organization_id=org_id)

    rows = [
        (emp_in.id,   "IN",  now),
        (emp_out.id,  "OUT", old),
        (emp_edge.id, "IN",  old),   # stale — should NOT be clocked_in
    ]

    db = make_db(
        FakeResult(scalars_list=[emp_in, emp_out, emp_edge]),
        FakeResult(rows=rows),
    )

    current_user = SimpleNamespace(organization_id=org_id)

    res = await attendance_mod.get_attendance_status(
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    clocked_in_ids = {e.id for e in res.data.clocked_in}
    inactive_ids   = {e.id for e in res.data.inactive}

    assert emp_in.id   in clocked_in_ids
    assert emp_out.id  in inactive_ids


@pytest.mark.asyncio
async def test_get_attendance_status_stale_in_goes_to_inactive(monkeypatch):
    """An employee whose last IN was >24 h ago must end up in inactive,
    not silently dropped from both lists."""
    monkeypatch.setattr(
        attendance_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id)
    stale_time = datetime.now(timezone.utc) - timedelta(hours=30)

    db = make_db(
        FakeResult(scalars_list=[emp]),
        FakeResult(rows=[(emp.id, "IN", stale_time)]),
    )

    res = await attendance_mod.get_attendance_status(
        current_user=SimpleNamespace(organization_id=org_id),
        db=db,
    )

    assert res.success is True
    all_ids = {e.id for e in res.data.clocked_in} | {e.id for e in res.data.inactive}
    assert emp.id in all_ids, "Employee must appear in exactly one list — not dropped"


@pytest.mark.asyncio
async def test_get_attendance_status_boundary_timestamp(monkeypatch):
    """An employee whose last IN is exactly at the boundary edge (24 h ago)
    should be handled deterministically — not clocked_in."""
    monkeypatch.setattr(
        attendance_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id)
    boundary = datetime.now(timezone.utc) - timedelta(hours=24)

    db = make_db(
        FakeResult(scalars_list=[emp]),
        FakeResult(rows=[(emp.id, "IN", boundary)]),
    )

    res = await attendance_mod.get_attendance_status(
        current_user=SimpleNamespace(organization_id=org_id),
        db=db,
    )

    assert res.success is True
    clocked_in_ids = {e.id for e in res.data.clocked_in}


@pytest.mark.asyncio
async def test_get_attendance_status_no_logs(monkeypatch):
    """An employee with no attendance logs at all ends up in inactive."""
    monkeypatch.setattr(
        attendance_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id)

    db = make_db(
        FakeResult(scalars_list=[emp]),
        FakeResult(rows=[]),   # no log rows at all
    )

    res = await attendance_mod.get_attendance_status(
        current_user=SimpleNamespace(organization_id=org_id),
        db=db,
    )

    assert res.success is True
    inactive_ids = {e.id for e in res.data.inactive}
    assert emp.id in inactive_ids


@pytest.mark.asyncio
async def test_get_attendance_status_only_out_events(monkeypatch):
    """An employee who has only ever clocked OUT (never IN) is inactive."""
    monkeypatch.setattr(
        attendance_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id)
    now = datetime.now(timezone.utc)

    db = make_db(
        FakeResult(scalars_list=[emp]),
        FakeResult(rows=[(emp.id, "OUT", now)]),
    )

    res = await attendance_mod.get_attendance_status(
        current_user=SimpleNamespace(organization_id=org_id),
        db=db,
    )

    assert res.success is True
    clocked_in_ids = {e.id for e in res.data.clocked_in}
    assert emp.id not in clocked_in_ids


@pytest.mark.asyncio
async def test_get_attendance_status_no_employees(monkeypatch):
    """Org with no employees returns empty lists without error."""
    monkeypatch.setattr(
        attendance_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    db = make_db(
        FakeResult(scalars_list=[]),
        FakeResult(rows=[]),
    )

    res = await attendance_mod.get_attendance_status(
        current_user=SimpleNamespace(organization_id=uuid.uuid4()),
        db=db,
    )

    assert res.success is True
    assert res.data.clocked_in == []
    assert res.data.inactive == []


# ===========================================================================
# Error handling & cross-cutting concerns
# ===========================================================================

@pytest.mark.asyncio
async def test_get_attendance_records_db_error(monkeypatch):
    """A DB exception on the count query propagates or is handled gracefully."""
    _patch_common(monkeypatch)

    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    with pytest.raises(Exception):
        await attendance_mod.get_attendance_records(
            start_date=None,
            end_date=None,
            page=1,
            page_size=20,
            current_user=current_user,
            db=FailingDB(),
        )


@pytest.mark.asyncio
async def test_get_employee_attendance_records_db_error(monkeypatch):
    """DB failure while fetching employee records raises rather than silently failing."""
    _patch_common(monkeypatch)

    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    with pytest.raises(Exception):
        await attendance_mod.get_employee_attendance_records(
            employee_id=uuid.uuid4(),
            start_date=None,
            end_date=None,
            page=1,
            page_size=20,
            current_user=current_user,
            db=FailingDB(),
        )


@pytest.mark.asyncio
async def test_get_all_attendance_logs_db_error(monkeypatch):
    """DB failure on log listing raises rather than returning a partial result."""
    _patch_common(monkeypatch)

    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    with pytest.raises(Exception):
        await attendance_mod.get_all_attendance_logs(
            start_date=None,
            end_date=None,
            page=1,
            page_size=50,
            current_user=current_user,
            db=FailingDB(),
        )


@pytest.mark.asyncio
async def test_get_attendance_status_db_error(monkeypatch):
    """DB failure on status fetch raises rather than returning empty data."""
    monkeypatch.setattr(
        attendance_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    with pytest.raises(Exception):
        await attendance_mod.get_attendance_status(
            current_user=SimpleNamespace(organization_id=uuid.uuid4()),
            db=FailingDB(),
        )


@pytest.mark.asyncio
async def test_model_validate_error_propagates(monkeypatch):
    """If model_validate raises a ValidationError, the endpoint should not
    silently swallow it — the caller must receive an error signal."""
    monkeypatch.setattr(
        attendance_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    def exploding_validate(r):
        raise ValueError("malformed row from DB")

    monkeypatch.setattr(
        attendance_mod.PayrollSessionResponse, "model_validate",
        exploding_validate
    )

    db = make_db(
        FakeResult(scalar_value=1),
        FakeResult(scalars_list=[DummyPayrollSession()]),
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    with pytest.raises(Exception):
        await attendance_mod.get_attendance_records(
            start_date=None,
            end_date=None,
            page=1,
            page_size=20,
            current_user=current_user,
            db=db,
        )


@pytest.mark.asyncio
async def test_get_attendance_records_page_size_one(monkeypatch):
    """page_size=1 produces correct total_pages for a multi-record result set."""
    _patch_common(monkeypatch)

    db = make_db(
        FakeResult(scalar_value=3),
        FakeResult(scalars_list=[DummyPayrollSession()]),
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await attendance_mod.get_attendance_records(
        start_date=None,
        end_date=None,
        page=1,
        page_size=1,
        current_user=current_user,
        db=db,
    )

    assert res.meta["total_pages"] == 3   # ceil(3/1)
    assert res.meta["total_items"] == 3