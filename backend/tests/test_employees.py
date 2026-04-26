import pytest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.routes import employees as employees_mod


# ---------------------------------------------------------------------------
# Fake DB helpers
# ---------------------------------------------------------------------------

class FakeResult:
    def __init__(self, scalar_value=None, scalars_list=None, first_value=None):
        self._scalar = scalar_value
        self._scalars = scalars_list or []
        self._first = first_value

    def scalar(self):
        return self._scalar

    def scalars(self):
        return FakeScalars(self._scalars, self._first)

    def first(self):
        # For result.first() used in verify (returns row tuples)
        return self._first


class FakeScalars:
    def __init__(self, items, first_value=None):
        self._items = items
        self._first = first_value

    def first(self):
        return self._first

    def all(self):
        return self._items


def make_db(*results):
    results = list(results)
    call_count = {"n": 0}

    async def execute(q):
        idx = call_count["n"]
        call_count["n"] += 1
        return results[idx]

    async def flush(): pass
    async def commit(): pass
    async def rollback(): pass

    added = []

    async def refresh(obj):
        if not hasattr(obj, "id") or obj.id is None:
            obj.id = uuid.uuid4()
        if not hasattr(obj, "created_at"):
            obj.created_at = datetime.now(timezone.utc)
        if not hasattr(obj, "updated_at"):
            obj.updated_at = datetime.now(timezone.utc)

    def add(obj):
        if not hasattr(obj, "id") or obj.id is None:
            obj.id = uuid.uuid4()
        added.append(obj)

    return SimpleNamespace(
        execute=execute,
        flush=flush,
        commit=commit,
        rollback=rollback,
        refresh=refresh,
        add=add,
        _added=added,
    )


# ---------------------------------------------------------------------------
# Dummy models
# ---------------------------------------------------------------------------

class DummyEmployee:
    def __init__(self, id=None, organization_id=None, name="Test Employee",
                 hourly_rate=15.0, email="test@test.com"):
        self.id = id or uuid.uuid4()
        self.organization_id = organization_id or uuid.uuid4()
        self.name = name
        self.hourly_rate = hourly_rate
        self.email = email
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class DummyAttendanceLog:
    def __init__(self, employee_id=None, action="IN", timestamp=None):
        self.id = uuid.uuid4()
        self.employee_id = employee_id or uuid.uuid4()
        self.action = action
        self.timestamp = timestamp or datetime.now(timezone.utc)


class DummyEmployeeCreate:
    def __init__(self, org_id=None):
        self.name = "New Employee"
        self.hourly_rate = 20.0
        self.email = "new@test.com"
        self.embedding = [0.1] * 512

    def model_dump(self):
        return {
            "name": self.name,
            "hourly_rate": self.hourly_rate,
            "email": self.email,
            "embedding": self.embedding,
        }


class DummyEmployeeUpdate:
    def __init__(self, name="Updated Name", hourly_rate=25.0):
        self.name = name
        self.hourly_rate = hourly_rate

    def model_dump(self, exclude_unset=False):
        return {"name": self.name, "hourly_rate": self.hourly_rate}


# ---------------------------------------------------------------------------
# /employees GET tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_employees_pagination(monkeypatch):
    monkeypatch.setattr(
        employees_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )
    monkeypatch.setattr(
        employees_mod.EmployeeResponse, "model_validate",
        lambda r: {"id": str(r.id), "name": r.name}
    )

    org_id = uuid.uuid4()
    emp1 = DummyEmployee(organization_id=org_id)
    emp2 = DummyEmployee(organization_id=org_id)

    db = make_db(
        FakeResult(scalar_value=2),                   # count query
        FakeResult(scalars_list=[emp1, emp2]),         # fetch query
    )
    current_user = SimpleNamespace(organization_id=org_id)

    res = await employees_mod.get_employees(
        current_user=current_user,
        db=db,
        page=1,
        page_size=50,
    )

    assert res.success is True
    assert len(res.data) == 2
    assert res.meta["total_items"] == 2
    assert res.meta["total_pages"] == 1


@pytest.mark.asyncio
async def test_get_employees_empty(monkeypatch):
    monkeypatch.setattr(
        employees_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )
    monkeypatch.setattr(
        employees_mod.EmployeeResponse, "model_validate",
        lambda r: {"id": str(r.id)}
    )

    db = make_db(
        FakeResult(scalar_value=0),
        FakeResult(scalars_list=[]),
    )
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await employees_mod.get_employees(
        current_user=current_user,
        db=db,
        page=1,
        page_size=50,
    )

    assert res.success is True
    assert res.data == []
    assert res.meta["total_items"] == 0
    assert res.meta["total_pages"] == 0


# ---------------------------------------------------------------------------
# /employees POST tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_employee_success():
    org_id = uuid.uuid4()
    current_user = SimpleNamespace(organization_id=org_id)

    db = make_db()  # no execute calls needed — just add/commit/refresh
    employee_data = DummyEmployeeCreate()

    res = await employees_mod.add_employee(
        employee=employee_data,
        current_user=current_user,
        db=db,
    )

    # Returns APIResponse directly
    assert res.success is True
    assert res.message == "Employee added successfully"
    # Confirm the record was added to db
    assert len(db._added) == 1
    assert db._added[0].organization_id == org_id


@pytest.mark.asyncio
async def test_add_employee_db_failure(monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError

    org_id = uuid.uuid4()
    current_user = SimpleNamespace(organization_id=org_id)

    async def bad_commit():
        raise SQLAlchemyError("DB error")

    db = make_db()
    db.commit = bad_commit

    res = await employees_mod.add_employee(
        employee=DummyEmployeeCreate(),
        current_user=current_user,
        db=db,
    )

    assert res.success is False
    assert "Failed to add employee" in res.message


# ---------------------------------------------------------------------------
# /employees PUT tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_edit_employee_success():
    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id)
    current_user = SimpleNamespace(organization_id=org_id)

    db = make_db(FakeResult(first_value=emp))

    res = await employees_mod.edit_employee(
        employee_id=emp.id,
        employee=DummyEmployeeUpdate(name="Updated Name", hourly_rate=25.0),
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert emp.name == "Updated Name"
    assert emp.hourly_rate == 25.0


@pytest.mark.asyncio
async def test_edit_employee_not_found(monkeypatch):
    monkeypatch.setattr(
        employees_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    db = make_db(FakeResult(first_value=None))  # employee not found
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await employees_mod.edit_employee(
        employee_id=uuid.uuid4(),
        employee=DummyEmployeeUpdate(),
        current_user=current_user,
        db=db,
    )

    assert res.success is False
    assert "not found" in res.message


@pytest.mark.asyncio
async def test_edit_employee_db_failure(monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError

    monkeypatch.setattr(
        employees_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id)
    current_user = SimpleNamespace(organization_id=org_id)

    async def bad_commit():
        raise SQLAlchemyError("DB error")

    db = make_db(FakeResult(first_value=emp))
    db.commit = bad_commit

    res = await employees_mod.edit_employee(
        employee_id=emp.id,
        employee=DummyEmployeeUpdate(),
        current_user=current_user,
        db=db,
    )

    assert res.success is False
    assert "Failed to update" in res.message


# ---------------------------------------------------------------------------
# /employees/verify POST tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verify_clock_in(monkeypatch):
    """Employee with no prior log gets clocked IN."""
    monkeypatch.setattr(
        employees_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )
    # Suppress websocket broadcast
    async def mock_broadcast(org_id, payload): pass
    monkeypatch.setattr(
        employees_mod.org_ws_manager, "broadcast_to_org", mock_broadcast
    )

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id)
    current_user = SimpleNamespace(organization_id=org_id)

    db = make_db(
        FakeResult(first_value=(emp, 0.95)),  # similarity query → (employee, score)
        FakeResult(first_value=None),          # last_log → no prior log, so action = IN
    )

    request = SimpleNamespace(embedding=[0.1] * 512)

    res = await employees_mod.verify(
        request=request,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert res.data["action"] == "IN"
    assert res.data["verified"] is True


@pytest.mark.asyncio
async def test_verify_clock_out(monkeypatch):
    """Employee whose last log is IN gets clocked OUT and creates a payroll session."""
    monkeypatch.setattr(
        employees_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )
    async def mock_broadcast(org_id, payload): pass
    monkeypatch.setattr(
        employees_mod.org_ws_manager, "broadcast_to_org", mock_broadcast
    )

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id, hourly_rate=20.0)
    clock_in_log = DummyAttendanceLog(
        employee_id=emp.id,
        action="IN",
        timestamp=datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
    )
    current_user = SimpleNamespace(organization_id=org_id)

    db = make_db(
        FakeResult(first_value=(emp, 0.92)),    # similarity query
        FakeResult(first_value=clock_in_log),   # last_log → IN, so action = OUT
        FakeResult(first_value=clock_in_log),   # clock_in fetch for payroll session
    )

    request = SimpleNamespace(embedding=[0.1] * 512)

    res = await employees_mod.verify(
        request=request,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert res.data["action"] == "OUT"
    assert "payroll_session" in res.data
    assert res.data["payroll_session"]["total_hours"] > 0


@pytest.mark.asyncio
async def test_verify_no_match(monkeypatch):
    """No employee found returns 404 response."""
    monkeypatch.setattr(
        employees_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    db = make_db(FakeResult(first_value=None))  # no match
    current_user = SimpleNamespace(organization_id=uuid.uuid4())
    request = SimpleNamespace(embedding=[0.1] * 512)

    res = await employees_mod.verify(
        request=request,
        current_user=current_user,
        db=db,
    )

    assert res.success is False
    assert "No matching" in res.message


@pytest.mark.asyncio
async def test_verify_below_threshold(monkeypatch):
    """Similarity below threshold returns 404 response."""
    monkeypatch.setattr(
        employees_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    org_id = uuid.uuid4()
    emp = DummyEmployee(organization_id=org_id)

    # Similarity of 0.5 is below the 0.7 threshold
    db = make_db(FakeResult(first_value=(emp, 0.5)))
    current_user = SimpleNamespace(organization_id=org_id)
    request = SimpleNamespace(embedding=[0.1] * 512)

    res = await employees_mod.verify(
        request=request,
        current_user=current_user,
        db=db,
    )

    assert res.success is False
    assert "No matching" in res.message


@pytest.mark.asyncio
async def test_verify_invalid_embedding_length(monkeypatch):
    """Wrong embedding dimension returns failure without hitting the DB."""
    monkeypatch.setattr(
        employees_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    db = make_db()
    current_user = SimpleNamespace(organization_id=uuid.uuid4())
    request = SimpleNamespace(embedding=[0.1] * 256)  # wrong size

    res = await employees_mod.verify(
        request=request,
        current_user=current_user,
        db=db,
    )

    assert res.success is False
    assert "512" in res.message