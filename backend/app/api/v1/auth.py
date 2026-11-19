from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User, UserRole, Farmer
from app.models.location import FarmerLocation
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


# normalize_phone_number moved to app.core.phone (shared, non-router module) so
# services can import it without depending on an API router. Re-exported here for
# backward compatibility (existing callers such as farmers.py import it from here).
from app.core.phone import normalize_phone_number  # noqa: F401  (re-export)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserRegister, db: Session = Depends(get_db)):
    """
    Registers a new user (Farmer, Agronomist, or Admin).
    If registered as a Farmer, automatically creates their farmer profile
    and initial farm location in Rwanda.
    """
    phone = normalize_phone_number(user_in.phone_number)

    # Check for existing phone number
    existing_user = db.query(User).filter(User.phone_number == phone).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this phone number is already registered.",
        )

    # Check for existing email if provided
    if user_in.email:
        existing_email = db.query(User).filter(User.email == user_in.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email is already registered.",
            )

    # Create base user
    new_user = User(
        phone_number=phone,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=True,
        is_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # If role is FARMER, create farmer profile & location
    if new_user.role == UserRole.FARMER:
        farmer_profile = Farmer(
            user_id=new_user.id,
            national_id=user_in.national_id,
            preferred_language=user_in.preferred_language,
            cooperative_name=user_in.cooperative_name,
            is_phone_verified=True,
        )
        db.add(farmer_profile)
        db.commit()
        db.refresh(farmer_profile)

        # Create primary location if district is provided
        if user_in.district:
            location = FarmerLocation(
                farmer_id=farmer_profile.id,
                province=user_in.province or "Northern Province",
                district=user_in.district,
                sector=user_in.sector or "Muhoza",
                cell=user_in.cell,
                village=user_in.village,
                latitude=user_in.latitude,
                longitude=user_in.longitude,
                is_primary=True,
            )
            db.add(location)
            db.commit()

    # Generate JWT access token
    access_token = create_access_token(
        subject=new_user.phone_number,
        role=new_user.role.value,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=new_user.role.value,
        user_id=new_user.id,
        phone_number=new_user.phone_number,
        full_name=new_user.full_name,
    )


@router.post("/login", response_model=Token)
def login_user(login_in: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates a user by phone number (or email) and password.
    Returns a signed JWT access token.
    """
    phone = normalize_phone_number(login_in.phone_number)
    user = (
        db.query(User).filter(User.phone_number == phone).first()
        or db.query(User).filter(User.email == login_in.phone_number).first()
    )

    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account has been deactivated.",
        )

    access_token = create_access_token(
        subject=user.phone_number,
        role=user.role.value,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role.value,
        user_id=user.id,
        phone_number=user.phone_number,
        full_name=user.full_name,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieves the currently authenticated user's account details.
    """
    return current_user
