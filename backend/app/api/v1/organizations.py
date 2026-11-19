from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, get_current_admin
from app.models.user import (
    User,
    UserRole,
    Organization,
    OrganizationType,
    OrganizationMember,
    OrganizationMemberRole,
    Agronomist,
    Farmer,
)
from app.models.report import CropReport
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationMemberResponse,
    AssignMemberRequest,
)
from app.schemas.report import CropReportResponse
from app.api.v1.reports import format_report_response

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def format_org_response(org: Organization, db: Session) -> OrganizationResponse:
    """Helper to convert Organization model to response schema with member count."""
    member_count = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org.id).count()
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        code=org.code,
        type=org.type,
        district=org.district,
        description=org.description,
        is_active=org.is_active,
        member_count=member_count,
        created_at=org.created_at,
    )


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_in: OrganizationCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Registers a new agricultural organization, cooperative, or agency.
    Restricted to System Administrators.
    """
    existing = db.query(Organization).filter(
        (Organization.code == org_in.code) | (Organization.name == org_in.name)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An organization with this name or code already exists.",
        )

    new_org = Organization(
        name=org_in.name,
        code=org_in.code,
        type=org_in.type,
        district=org_in.district,
        description=org_in.description,
        is_active=True,
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return format_org_response(new_org, db)


@router.get("/", response_model=List[OrganizationResponse])
def list_organizations(
    org_type: Optional[OrganizationType] = Query(None, description="Filter by organization type"),
    district: Optional[str] = Query(None, description="Filter by district"),
    is_active: bool = Query(True, description="Filter active organizations"),
    db: Session = Depends(get_db),
):
    """
    Lists agricultural organizations (RAB, farmer cooperatives, and NGOs).
    """
    query = db.query(Organization).filter(Organization.is_active == is_active)
    if org_type:
        query = query.filter(Organization.type == org_type)
    if district:
        query = query.filter(Organization.district.ilike(f"%{district}%"))

    orgs = query.all()
    return [format_org_response(o, db) for o in orgs]


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization_detail(org_id: int, db: Session = Depends(get_db)):
    """
    Retrieves detailed organization information.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    return format_org_response(org, db)


@router.put("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: int,
    org_in: OrganizationUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Updates organization details. Restricted to System Administrators.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    if org_in.name is not None:
        org.name = org_in.name
    if org_in.district is not None:
        org.district = org_in.district
    if org_in.description is not None:
        org.description = org_in.description
    if org_in.is_active is not None:
        org.is_active = org_in.is_active

    db.commit()
    db.refresh(org)
    return format_org_response(org, db)


@router.get("/{org_id}/members", response_model=List[OrganizationMemberResponse])
def list_organization_members(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists agronomists and administrators belonging to this organization.
    """
    members = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org_id).all()
    results = []
    for m in members:
        results.append(
            OrganizationMemberResponse(
                id=m.id,
                organization_id=m.organization_id,
                user_id=m.user_id,
                full_name=m.user.full_name,
                phone_number=m.user.phone_number,
                role=m.role,
                created_at=m.created_at,
            )
        )
    return results


@router.post("/{org_id}/members", response_model=OrganizationMemberResponse, status_code=status.HTTP_201_CREATED)
def assign_member_to_organization(
    org_id: int,
    assign_in: AssignMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Assigns a user or agronomist to the organization with a designated role.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    user = db.query(User).filter(User.id == assign_in.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Check if already a member
    existing = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == user.id,
    ).first()

    if existing:
        existing.role = assign_in.role
        db.commit()
        db.refresh(existing)
        member = existing
    else:
        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=assign_in.role,
        )
        db.add(member)
        db.commit()
        db.refresh(member)

    # If user has an agronomist profile, link their organization_id
    if user.agronomist_profile:
        user.agronomist_profile.organization_id = org.id
        db.commit()

    return OrganizationMemberResponse(
        id=member.id,
        organization_id=member.organization_id,
        user_id=user.id,
        full_name=user.full_name,
        phone_number=user.phone_number,
        role=member.role,
        created_at=member.created_at,
    )


@router.get("/{org_id}/reports", response_model=List[CropReportResponse])
def get_organization_reports(
    org_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves reports belonging to the organization's jurisdiction
    (either matched by cooperative name or district coverage).
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    query = db.query(CropReport)
    if org.type == OrganizationType.COOPERATIVE:
        # Match by cooperative farmers
        query = query.join(Farmer).filter(Farmer.cooperative_name.ilike(f"%{org.code}%"))
    elif org.district:
        query = query.filter(CropReport.district.ilike(f"%{org.district}%"))

    reports = query.order_by(CropReport.created_at.desc()).offset(skip).limit(limit).all()
    return [format_report_response(r) for r in reports]
