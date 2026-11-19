from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against the stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashes a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Creates a cryptographically signed JWT access token.
    Subject is typically the user ID or unique phone number.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "role": role,
        "iat": now,
        "exp": expire,
    }

    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a JWT access token.
    Returns the token payload if valid, or None if expired or invalid.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return None
