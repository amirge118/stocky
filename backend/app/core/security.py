from datetime import datetime, timedelta
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# Use bcrypt directly; passlib 1.7.4 + bcrypt 5 can raise spurious 72-byte errors on hash/verify.
_BCRYPT_MAX_PASSWORD_BYTES = 72
_BCRYPT_DEFAULT_ROUNDS = 12


def _password_bytes_for_bcrypt(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_PASSWORD_BYTES]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    try:
        return bcrypt.checkpw(
            _password_bytes_for_bcrypt(plain_password),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    """Hash a password."""
    salt = bcrypt.gensalt(rounds=_BCRYPT_DEFAULT_ROUNDS)
    hashed = bcrypt.hashpw(_password_bytes_for_bcrypt(password), salt)
    return hashed.decode("ascii")


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None
