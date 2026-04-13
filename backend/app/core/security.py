from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import base64
import hashlib
import hmac
import os

from jose import jwt

from app.core.config import settings

PBKDF2_ITERATIONS = 260000
PBKDF2_SCHEME = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    salt_b64 = base64.b64encode(salt).decode("ascii")
    digest_b64 = base64.b64encode(digest).decode("ascii")
    return "{}${}${}${}".format(PBKDF2_SCHEME, PBKDF2_ITERATIONS, salt_b64, digest_b64)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        scheme, iterations_raw, salt_b64, digest_b64 = password_hash.split("$", 3)
        if scheme != PBKDF2_SCHEME:
            return False
        iterations = int(iterations_raw)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(digest_b64.encode("ascii"))
    except Exception:
        return False

    actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire_delta = timedelta(minutes=expires_minutes or settings.jwt_access_token_expire_minutes)
    expire_at = datetime.now(timezone.utc) + expire_delta
    payload: Dict[str, Any] = {"sub": subject, "exp": expire_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
