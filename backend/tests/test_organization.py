import pytest
import uuid
from datetime import time
from types import SimpleNamespace

from app.routes import organization as organizations_mod


# ---------------------------------------------------------------------------
# Fake DB helpers
# ---------------------------------------------------------------------------

class FakeResult:
    def __init__(self, scalar_one_or_none_value=None):
        self._value = scalar_one_or_none_value

    def scalar_one_or_none(self):
        return self._value


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

class DummyOrg:
    def __init__(self, id=None, open_time=None, close_time=None):
        self.id = id or uuid.uuid4()
        self.default_open_time = open_time
        self.default_close_time = close_time


class DummyOrganizationRequest:
    def __init__(self, open_time=None, close_time=None):
        self.default_open_time = open_time or time(9, 0)
        self.default_close_time = close_time or time(17, 0)

    def model_dump(self, exclude_unset=False):
        return {
            "default_open_time": self.default_open_time,
            "default_close_time": self.default_close_time,
        }


# ---------------------------------------------------------------------------
# POST / (add_times) tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_times_success():
    """Sets open/close times when org exists and times are not yet set."""
    org = DummyOrg(open_time=None, close_time=None)
    current_user = SimpleNamespace(organization_id=org.id)
    db = make_db(FakeResult(scalar_one_or_none_value=org))

    res = await organizations_mod.add_times(
        request=DummyOrganizationRequest(time(9, 0), time(17, 0)),
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert res.message == "Open/Close times added successfully"
    assert org.default_open_time == time(9, 0)
    assert org.default_close_time == time(17, 0)


@pytest.mark.asyncio
async def test_add_times_org_not_found(monkeypatch):
    """Returns failure when org doesn't exist."""
    monkeypatch.setattr(
        organizations_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    db = make_db(FakeResult(scalar_one_or_none_value=None))
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await organizations_mod.add_times(
        request=DummyOrganizationRequest(),
        current_user=current_user,
        db=db,
    )

    assert res.success is False
    assert "not found" in res.message


@pytest.mark.asyncio
async def test_add_times_already_set(monkeypatch):
    """Returns failure when times are already set."""
    monkeypatch.setattr(
        organizations_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    org = DummyOrg(open_time=time(8, 0), close_time=time(16, 0))
    current_user = SimpleNamespace(organization_id=org.id)
    db = make_db(FakeResult(scalar_one_or_none_value=org))

    res = await organizations_mod.add_times(
        request=DummyOrganizationRequest(),
        current_user=current_user,
        db=db,
    )

    assert res.success is False
    assert "already set" in res.message


# ---------------------------------------------------------------------------
# PUT / (update_times) tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_times_success():
    """Updates open/close times on an existing org."""
    org = DummyOrg(open_time=time(8, 0), close_time=time(16, 0))
    current_user = SimpleNamespace(organization_id=org.id)
    db = make_db(FakeResult(scalar_one_or_none_value=org))

    res = await organizations_mod.update_times(
        request=DummyOrganizationRequest(time(10, 0), time(18, 0)),
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert res.message == "Open/Close times updated successfully"
    assert org.default_open_time == time(10, 0)
    assert org.default_close_time == time(18, 0)


@pytest.mark.asyncio
async def test_update_times_org_not_found(monkeypatch):
    """Returns failure when org doesn't exist."""
    monkeypatch.setattr(
        organizations_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    db = make_db(FakeResult(scalar_one_or_none_value=None))
    current_user = SimpleNamespace(organization_id=uuid.uuid4())

    res = await organizations_mod.update_times(
        request=DummyOrganizationRequest(),
        current_user=current_user,
        db=db,
    )

    assert res.success is False
    assert "not found" in res.message


@pytest.mark.asyncio
async def test_update_times_partial_update():
    """Only the fields provided in the request are updated."""
    org = DummyOrg(open_time=time(8, 0), close_time=time(16, 0))
    current_user = SimpleNamespace(organization_id=org.id)
    db = make_db(FakeResult(scalar_one_or_none_value=org))

    # Only update open_time, leave close_time as-is
    request = DummyOrganizationRequest()
    request.model_dump = lambda exclude_unset=False: {"default_open_time": time(11, 0)}

    res = await organizations_mod.update_times(
        request=request,
        current_user=current_user,
        db=db,
    )

    assert res.success is True
    assert org.default_open_time == time(11, 0)
    assert org.default_close_time == time(16, 0)  # unchanged