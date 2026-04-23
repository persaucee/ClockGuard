import json
import pytest
import uuid
from datetime import datetime, timezone, time
from types import SimpleNamespace

from app.routes import auth as auth_mod


# ---------------------------------------------------------------------------
# Fake DB helper
# ---------------------------------------------------------------------------

class FakeResult:
    def __init__(self, first_value=None):
        self._first = first_value

    def scalars(self):
        return self

    def first(self):
        return self._first


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

    # refresh populates org fields needed by RegisterDataResponse
    async def refresh(obj):
        if not hasattr(obj, "username"):  # it's an Org
            obj.id = obj.id if hasattr(obj, "id") else uuid.uuid4()
            obj.name = getattr(obj, "name", "Test Org")
            obj.default_open_time = getattr(obj, "default_open_time", None)
            obj.default_close_time = getattr(obj, "default_close_time", None)

    def add(obj):
        # Assign an id when added, simulating DB insert
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

class DummyAdmin:
    def __init__(self, username="testadmin", organization_id=None,
                 password_hash="hashed", two_factor_enabled=False,
                 two_factor_secret=None):
        self.id = uuid.uuid4()
        self.username = username
        self.organization_id = organization_id or uuid.uuid4()
        self.password_hash = password_hash
        self.first_name = "Test"
        self.last_name = "Admin"
        self.two_factor_enabled = two_factor_enabled
        self.two_factor_secret = two_factor_secret
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class DummyRegisterRequest:
    def __init__(self):
        self.username = "newadmin"
        self.password = "securepassword"
        self.organization_name = "Test Org"
        self.first_name = "New"
        self.last_name = "Admin"
        self.open_time = time(9, 0)     # ← must be time objects, not strings
        self.close_time = time(17, 0)


class DummyLoginData:
    def __init__(self, username="testadmin", password="password123"):
        self.username = username
        self.password = password


# ---------------------------------------------------------------------------
# Cookie assertion helper
# ---------------------------------------------------------------------------

def get_all_cookies(response) -> str:
    """Joins all set-cookie headers into one string for easy assertions."""
    return " ".join(response.headers.getlist("set-cookie"))


# ---------------------------------------------------------------------------
# /register tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_success(monkeypatch):
    """New username registers successfully and sets auth cookies."""
    db = make_db(FakeResult(first_value=None))  # no existing user

    async def mock_run_in_threadpool(func, *args):
        return "hashed_password"
    monkeypatch.setattr(auth_mod, "run_in_threadpool", mock_run_in_threadpool)

    form_data = DummyRegisterRequest()
    response = await auth_mod.register(form_data=form_data, db=db)

    body = json.loads(response.body)
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["username"] == "newadmin"

    cookies = get_all_cookies(response)
    assert "access_token" in cookies
    assert "refresh_token" in cookies


@pytest.mark.asyncio
async def test_register_duplicate_username(monkeypatch):
    """Registration fails when username is already taken."""
    existing = DummyAdmin(username="takenuser")
    db = make_db(FakeResult(first_value=existing))

    async def mock_run_in_threadpool(func, *args):
        return "hashed_password"
    monkeypatch.setattr(auth_mod, "run_in_threadpool", mock_run_in_threadpool)

    form_data = DummyRegisterRequest()
    form_data.username = "takenuser"

    # Route returns create_response early — which is an APIResponse, not JSONResponse
    res = await auth_mod.register(form_data=form_data, db=db)
    body = json.loads(res.body)

    assert body["success"] is False
    assert "already exists" in body["message"]


# ---------------------------------------------------------------------------
# /login tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(monkeypatch):
    """Valid credentials return auth cookies."""
    admin = DummyAdmin(username="testadmin")
    db = make_db(FakeResult(first_value=admin))

    async def mock_run_in_threadpool(func, *args):
        return True  # password valid
    monkeypatch.setattr(auth_mod, "run_in_threadpool", mock_run_in_threadpool)

    response = await auth_mod.login(
        form_data=DummyLoginData(username="testadmin", password="password123"),
        db=db
    )

    assert response.status_code == 200
    body = json.loads(response.body)
    assert body["success"] is True

    cookies = get_all_cookies(response)
    assert "access_token" in cookies
    assert "refresh_token" in cookies


@pytest.mark.asyncio
async def test_login_wrong_password(monkeypatch):
    """Wrong password returns failure without setting cookies."""
    admin = DummyAdmin(username="testadmin")
    db = make_db(FakeResult(first_value=admin))

    async def mock_run_in_threadpool(func, *args):
        return False  # password invalid
    monkeypatch.setattr(auth_mod, "run_in_threadpool", mock_run_in_threadpool)

    res = await auth_mod.login(
        form_data=DummyLoginData(username="testadmin", password="wrongpass"),
        db=db
    )
    body = json.loads(res.body)

    assert body["success"] is False
    assert "Incorrect" in body["message"]
    assert "access_token" not in get_all_cookies(res)


@pytest.mark.asyncio
async def test_login_nonexistent_user(monkeypatch):
    """Unknown username returns failure without touching password check."""
    db = make_db(FakeResult(first_value=None))

    async def mock_run_in_threadpool(func, *args):
        return False
    monkeypatch.setattr(auth_mod, "run_in_threadpool", mock_run_in_threadpool)

    res = await auth_mod.login(
        form_data=DummyLoginData(username="ghost", password="password123"),
        db=db
    )
    body = json.loads(res.body)

    assert body["success"] is False
    assert "Incorrect" in body["message"]


@pytest.mark.asyncio
async def test_login_2fa_required(monkeypatch):
    """User with 2FA enabled receives temp token, no auth cookies."""
    admin = DummyAdmin(username="testadmin", two_factor_enabled=True)
    db = make_db(FakeResult(first_value=admin))

    async def mock_run_in_threadpool(func, *args):
        return True  # password valid
    monkeypatch.setattr(auth_mod, "run_in_threadpool", mock_run_in_threadpool)
    monkeypatch.setattr(auth_mod, "create_temp_2fa_token", lambda username: "temp_token_abc")

    response = await auth_mod.login(
        form_data=DummyLoginData(username="testadmin", password="password123"),
        db=db
    )
    body = json.loads(response.body)

    assert body["success"] is True
    assert body["data"]["two_factor_required"] is True
    assert body["data"]["temp_token"] == "temp_token_abc"
    assert "access_token" not in get_all_cookies(response)


# ---------------------------------------------------------------------------
# /refresh tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_token_success(monkeypatch):
    """Valid refresh token issues a new access token cookie."""
    monkeypatch.setattr(
        auth_mod.jwt, "decode",
        lambda token, secret, algorithms: {"sub": "testadmin", "type": "refresh"}
    )
    monkeypatch.setattr(
        auth_mod, "create_access_token",
        lambda data, **kwargs: "new_access_token_xyz"
    )

    request = SimpleNamespace(cookies={"refresh_token": "valid.refresh.token"})
    response = await auth_mod.refresh_token_endpoint(request=request)

    assert response.status_code == 200
    assert "access_token" in get_all_cookies(response)


@pytest.mark.asyncio
async def test_refresh_token_missing_cookie():
    """Missing refresh token cookie raises 401."""
    from fastapi import HTTPException

    request = SimpleNamespace(cookies={})
    with pytest.raises(HTTPException) as exc_info:
        await auth_mod.refresh_token_endpoint(request=request)

    assert exc_info.value.status_code == 401
    assert "missing" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_refresh_token_invalid_jwt(monkeypatch):
    """Malformed JWT raises 401."""
    from fastapi import HTTPException
    from jose import jwt as jose_jwt

    def raise_jwt_error(token, secret, algorithms):
        raise jose_jwt.JWTError("bad token")

    monkeypatch.setattr(auth_mod.jwt, "decode", raise_jwt_error)

    request = SimpleNamespace(cookies={"refresh_token": "bad.token.here"})
    with pytest.raises(HTTPException) as exc_info:
        await auth_mod.refresh_token_endpoint(request=request)

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# /me tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_read_users_me(monkeypatch):
    """Authenticated user gets their own info back."""
    monkeypatch.setattr(
        auth_mod, "create_response",
        lambda **kwargs: SimpleNamespace(**kwargs)
    )

    org_id = uuid.uuid4()
    current_user = DummyAdmin(username="testadmin", organization_id=org_id)

    res = await auth_mod.read_users_me(current_user=current_user)

    assert res.success is True
    assert res.data.username == "testadmin"
    assert res.data.organization_id == org_id