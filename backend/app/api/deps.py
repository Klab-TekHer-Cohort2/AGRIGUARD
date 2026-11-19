from typing import Generator, Optional
import secrets
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User, UserRole, Farmer, Agronomist

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)

# Shared-secret header for the USSD/IVR gateway caller (never JWT).
GATEWAY_SECRET_HEADER = "X-AgriGuard-Gateway-Secret"


def verify_gateway_secret(
    x_agriguard_gateway_secret: Optional[str] = Header(default=None, alias=GATEWAY_SECRET_HEADER),
) -> None:
    """Reusable gate for USSD/IVR webhooks and the by-phone lookup endpoint.

    Constant-time comparison; fail-closed (503) when the secret is unset so an
    empty config never opens access; 401 on a missing/wrong header. Returns
    ``None`` (it is a gate, not a principal).
    """
    expected = settings.USSD_IVR_GATEWAY_SECRET
    if not expected:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="USSD/IVR gateway secret not configured.",
        )
    if not x_agriguard_gateway_secret or not secrets.compare_digest(
        x_agriguard_gateway_secret, expected
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid gateway secret.")
    return None


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides an active database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validates JWT bearer token and retrieves the current authenticated user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    phone_or_sub: str = payload.get("sub")
    if phone_or_sub is None:
        raise credentials_exception

    # User can be identified by phone_number or user_id
    user = db.query(User).filter(User.phone_number == phone_or_sub).first()
    if not user and phone_or_sub.isdigit():
        user = db.query(User).filter(User.id == int(phone_or_sub)).first()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")

    return user


def get_current_farmer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Farmer:
    """
    Ensures current authenticated user has an active Farmer profile.
    """
    if current_user.farmer_profile:
        return current_user.farmer_profile

    if current_user.role == UserRole.FARMER:
        # Create profile if not yet created
        profile = Farmer(
            user_id=current_user.id,
            preferred_language="rw",
            is_phone_verified=True,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="The user does not have a registered farmer profile.",
    )


def get_current_agronomist(
    current_user: User = Depends(get_current_user),
) -> Agronomist:
    """
    Ensures the user has an active Agronomist profile or is an admin.
    """
    if current_user.role in [UserRole.AGRONOMIST, UserRole.SYSTEM_ADMIN] and current_user.agronomist_profile:
        return current_user.agronomist_profile

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access restricted to authorized agronomists.",
    )


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Restricts access to System Administrators.
    """
    if current_user.role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required.",
        )
    return current_user
