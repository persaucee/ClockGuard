import os

from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from sqlalchemy import select

from .ws_manager import org_ws_manager
from app.models.User import Admin
from dependencies import get_db, get_token_from_cookie

router = APIRouter()
LOGIN_SECRET = os.getenv("LOGIN_SECRET")

async def get_admin_from_token(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
) -> Admin | None:
    """
    Mirrors get_current_user but reads from the session cookie
    instead of an Authorization header, since WS clients share
    the same cookie jar as your HTTP client.
    """
    try:
        token = get_token_from_cookie(websocket)  # Request and WebSocket both
    except Exception:                             # implement the MutableHeaders
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)  # interface, so this just works
        return None

    try:
        payload = jwt.decode(token, LOGIN_SECRET, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise ValueError("No subject")
    except (JWTError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    result = await db.execute(select(Admin).filter(Admin.username == username))
    admin = result.scalars().first()

    if admin is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    return admin


@router.websocket("/ws/admin/verify-feed")
async def admin_verify_feed(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):
    admin = await get_admin_from_token(websocket, db)
    if admin is None:
        return

    org_id: UUID = admin.organization_id
    await org_ws_manager.connect(websocket, org_id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await org_ws_manager.disconnect(websocket, org_id)