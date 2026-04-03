import os
import pyotp
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError

LOGIN_SECRET = os.getenv("LOGIN_SECRET")
TEMP_2FA_TOKEN_EXPIRE_MINUTES = int(os.getenv("TEMP_2FA_TOKEN_EXPIRE_MINUTES", 5))


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str, issuer: str = "ClockGuard") -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def verify_totp_code(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def create_temp_2fa_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TEMP_2FA_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "type": "pre_2fa",
        "exp": expire,
    }
    return jwt.encode(payload, LOGIN_SECRET, algorithm="HS256")


def decode_temp_2fa_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, LOGIN_SECRET, algorithms=["HS256"])
        if payload.get("type") != "pre_2fa":
            return None
        return payload.get("sub")
    except JWTError:
        return None