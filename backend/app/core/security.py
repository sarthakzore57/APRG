from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
import base64
import hashlib
import re

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings


def _password_bytes(password: str) -> bytes:
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(_password_bytes(password), hashed_password.encode("utf-8"))


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": subject, "exp": expires}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[get_settings().jwt_algorithm])
        subject = payload.get("sub")
        if not subject:
            raise ValueError("Missing token subject")
        return subject
    except (JWTError, ValueError) as exc:
        raise ValueError("Invalid authentication token") from exc


def safe_filename(filename: str) -> str:
    name = Path(filename).name
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return f"{uuid4().hex}_{stem or 'upload'}"


def assert_inside(base: Path, target: Path) -> None:
    base_resolved = base.resolve()
    target_resolved = target.resolve()
    if base_resolved != target_resolved and base_resolved not in target_resolved.parents:
        raise ValueError("Unsafe storage path")
