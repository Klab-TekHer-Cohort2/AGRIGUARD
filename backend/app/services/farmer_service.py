"""Farmer identification + self-registration service for USSD/IVR channels.

Imports from ``app.core.phone`` (shared, non-router) per finding #6 — never from
an API router module. ``self_register_farmer`` never raises ``HTTPException``
(finding #4): it runs inside ``menu.advance`` where a raised HTTPException would
break the CON/END contract. It is idempotent: a phone that already has a User
with a farmer profile returns that existing Farmer (menu -> MAIN_MENU); a phone
with a User but no farmer profile raises the typed ``FarmerAlreadyRegisteredError``
which the menu catches -> friendly END.
"""
import secrets
from typing import Optional
from sqlalchemy.orm import Session

from app.core.phone import normalize_phone_number
from app.core.security import get_password_hash
from app.models.user import User, UserRole, Farmer
from app.models.location import FarmerLocation


class FarmerAlreadyRegisteredError(Exception):
    """Raised when the phone already belongs to a non-farmer account (menu catches -> END)."""


def identify_farmer_by_phone(db: Session, phone: str) -> Optional[Farmer]:
    """Resolve a Farmer profile by (normalized) phone number, or None."""
    clean = normalize_phone_number(phone)
    user = db.query(User).filter(User.phone_number == clean).first()
    return user.farmer_profile if user and user.farmer_profile else None


def self_register_farmer(
    db: Session,
    phone: str,
    full_name: str,
    district: str,
    preferred_language: str = "rw",
) -> Farmer:
    """Idempotently create (or return) a Farmer for the given phone.

    - phone already has a User WITH a farmer profile -> return that Farmer
      (menu routes to MAIN_MENU with an "already registered" note).
    - phone already has a User WITHOUT a farmer profile (a non-farmer account)
      -> raise ``FarmerAlreadyRegisteredError`` (menu catches -> END "contact
      support"). No 409, no HTTPException.
    - phone unknown -> create a User + Farmer + primary location. Never asserts
      verification: ``is_phone_verified=False`` and ``User.is_verified=False``.
    """
    clean = normalize_phone_number(phone)
    user = db.query(User).filter(User.phone_number == clean).first()
    if user:  # idempotency: phone already known
        if user.farmer_profile:
            return user.farmer_profile  # already a farmer -> return it; menu -> MAIN_MENU
        raise FarmerAlreadyRegisteredError()  # non-farmer account -> menu catches -> END

    user = User(
        phone_number=clean,
        hashed_password=get_password_hash(secrets.token_urlsafe(32)),  # unusable; auth by phone
        full_name=full_name,
        role=UserRole.FARMER,
        is_active=True,
        is_verified=False,  # NOT verified (do not assert verification that didn't happen)
    )
    db.add(user)
    db.flush()
    farmer = Farmer(
        user_id=user.id,
        preferred_language=preferred_language,
        is_phone_verified=False,  # NOT verified
    )
    db.add(farmer)
    db.flush()
    db.add(
        FarmerLocation(
            farmer_id=farmer.id,
            district=district,
            sector="Unknown",
            is_primary=True,
        )
    )
    db.commit()
    db.refresh(farmer)
    return farmer
