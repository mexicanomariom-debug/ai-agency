import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import HTTPException, status

from config import settings


def validate_telegram_init_data(init_data: str, max_age_seconds: int = 86400) -> dict:
    """Validate Telegram Web App initData and return parsed user data."""
    if not init_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing init data")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing hash")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid init data")

    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > max_age_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Init data expired")

    user_data = json.loads(parsed.get("user", "{}"))
    if not user_data.get("id"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user data")

    return user_data


def get_demo_user() -> dict:
    return {
        "id": 0,
        "first_name": "Demo",
        "username": "demo_user",
    }
