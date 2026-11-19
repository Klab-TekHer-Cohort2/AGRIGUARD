import os
import sys
from pathlib import Path

# Ensure backend root is on Python sys.path
backend_root = str(Path(__file__).resolve().parent.parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import json
import logging
from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
import app.models  # Registers all 16 models with Base.metadata
from app.models.user import (
    User,
    UserRole,
    Farmer,
    Agronomist,
    Organization,
    OrganizationType,
    OrganizationMember,
    OrganizationMemberRole,
)
from app.models.location import FarmerLocation
from app.models.crop import Crop

logger = logging.getLogger("agriguard.init_db")

DEFAULT_CROPS = [
    {
        "name_en": "Maize",
        "name_rw": "Ibigori",
        "scientific_name": "Zea mays",
        "category": "CEREAL",
        "description": "Major staple cereal crop widely grown in Eastern and Northern provinces.",
        "common_pests": json.dumps(["Fall Armyworm", "Maize Stem Borer", "Maize Lethal Necrosis"])
    },
    {
        "name_en": "Irish Potato",
        "name_rw": "Ibirayi",
        "scientific_name": "Solanum tuberosum",
        "category": "TUBER",
        "description": "Crucial food security tuber intensively farmed in the volcanic highlands of Musanze and Nyabihu.",
        "common_pests": json.dumps(["Potato Late Blight", "Bacterial Wilt", "Potato Tuber Moth"])
    },
    {
        "name_en": "Banana",
        "name_rw": "Ibitoki",
        "scientific_name": "Musa spp.",
        "category": "FRUIT",
        "description": "Essential perennial cooking, brewing, and dessert banana crop across Rwanda.",
        "common_pests": json.dumps(["Banana Bacterial Wilt (BXW)", "Banana Weevil", "Fusarium Wilt"])
    },
    {
        "name_en": "Beans",
        "name_rw": "Ibishyimbo",
        "scientific_name": "Phaseolus vulgaris",
        "category": "LEGUME",
        "description": "Core protein source cultivated as climbing or bush beans throughout all districts.",
        "common_pests": json.dumps(["Bean Anthracnose", "Bean Fly", "Angular Leaf Spot", "Aphids"])
    },
    {
        "name_en": "Cassava",
        "name_rw": "Imyumbati",
        "scientific_name": "Manihot esculenta",
        "category": "TUBER",
        "description": "Drought-resilient root tuber grown predominantly in the Southern and Eastern provinces.",
        "common_pests": json.dumps(["Cassava Mosaic Disease (CMD)", "Cassava Brown Streak Disease", "Cassava Mealybug"])
    },
    {
        "name_en": "Rice",
        "name_rw": "Umuceri",
        "scientific_name": "Oryza sativa",
        "category": "CEREAL",
        "description": "Marshland staple grain grown in designated valleys and irrigation schemes.",
        "common_pests": json.dumps(["Rice Blast", "Bacterial Leaf Blight", "Stem Borer"])
    },
    {
        "name_en": "Tomato",
        "name_rw": "Inyanya",
        "scientific_name": "Solanum lycopersicum",
        "category": "VEGETABLE",
        "description": "High-value commercial horticultural crop grown in greenhouses and open fields.",
        "common_pests": json.dumps(["Tuta absoluta", "Tomato Late Blight", "Bacterial Canker"])
    },
    {
        "name_en": "Coffee",
        "name_rw": "Ikawa",
        "scientific_name": "Coffea arabica",
        "category": "CASH_CROP",
        "description": "Rwanda's leading export cash crop grown on steep highland slopes.",
        "common_pests": json.dumps(["Coffee Berry Borer", "Coffee Leaf Rust", "Antestia Bug"])
    }
]


def init_database(db: Session = None):
    """
    Creates all relational database tables and seeds initial administrative
    and agricultural reference data.
    """
    logger.info("Initializing relational database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("All 16 tables created or verified successfully.")

    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        # 1. Seed Default Crops
        for crop_data in DEFAULT_CROPS:
            existing = db.query(Crop).filter(Crop.name_en == crop_data["name_en"]).first()
            if not existing:
                crop = Crop(**crop_data)
                db.add(crop)
                logger.info(f"Seeded crop: {crop_data['name_en']} ({crop_data['name_rw']})")
        db.commit()

        # 2. Seed Default Organization (RAB)
        rab_org = db.query(Organization).filter(Organization.code == "RAB").first()
        if not rab_org:
            rab_org = Organization(
                name="Rwanda Agriculture and Animal Resources Development Board",
                code="RAB",
                type=OrganizationType.GOVERNMENT,
                district="Gasabo",
                description="National agency responsible for developing agriculture and animal resources in Rwanda."
            )
            db.add(rab_org)
            db.commit()
            db.refresh(rab_org)
            logger.info("Seeded organization: RAB")

        # 3. Seed Sample Cooperative
        coop = db.query(Organization).filter(Organization.code == "KOABIKI").first()
        if not coop:
            coop = Organization(
                name="Koperative y'Abahinzi b'Ibirayi mu Kinigi (KOABIKI)",
                code="KOABIKI",
                type=OrganizationType.COOPERATIVE,
                district="Musanze",
                description="Irish potato farmers cooperative operating in Kinigi, Musanze."
            )
            db.add(coop)
            db.commit()
            db.refresh(coop)
            logger.info("Seeded cooperative: KOABIKI")

        # 4. Seed Default System Admin
        admin_phone = "+250788000001"
        admin = db.query(User).filter(User.phone_number == admin_phone).first()
        if not admin:
            admin = User(
                phone_number=admin_phone,
                email="admin@agriguard.rw",
                hashed_password=get_password_hash("Admin2026!"),
                full_name="System Administrator",
                role=UserRole.SYSTEM_ADMIN,
                is_active=True,
                is_verified=True,
            )
            db.add(admin)
            db.commit()
            logger.info("Seeded default System Admin account.")

        # 5. Seed Sample Agronomist
        agro_phone = "+250788000002"
        agro_user = db.query(User).filter(User.phone_number == agro_phone).first()
        if not agro_user:
            agro_user = User(
                phone_number=agro_phone,
                email="emmanuel.mugisha@rab.gov.rw",
                hashed_password=get_password_hash("Agronomist2026!"),
                full_name="Emmanuel Mugisha",
                role=UserRole.AGRONOMIST,
                is_active=True,
                is_verified=True,
            )
            db.add(agro_user)
            db.commit()
            db.refresh(agro_user)

            agro_profile = Agronomist(
                user_id=agro_user.id,
                license_number="RAB-AGRO-2024-001",
                qualification="BSc Crop Protection & Soil Health",
                assigned_districts=json.dumps(["Musanze", "Nyabihu"]),
                assigned_sectors=json.dumps(["Muhoza", "Kinigi", "Busogo"]),
                organization_id=rab_org.id,
                is_active=True,
            )
            db.add(agro_profile)

            # Link agronomist to RAB organization
            member = OrganizationMember(
                organization_id=rab_org.id,
                user_id=agro_user.id,
                role=OrganizationMemberRole.LEAD_AGRONOMIST,
            )
            db.add(member)
            db.commit()
            logger.info("Seeded sample Agronomist: Emmanuel Mugisha")

        # 6. Seed Sample Farmer
        farmer_phone = "+250788111222"
        farmer_user = db.query(User).filter(User.phone_number == farmer_phone).first()
        if not farmer_user:
            farmer_user = User(
                phone_number=farmer_phone,
                email="mukamana@example.rw",
                hashed_password=get_password_hash("Farmer2026!"),
                full_name="Jeanne Mukamana",
                role=UserRole.FARMER,
                is_active=True,
                is_verified=True,
            )
            db.add(farmer_user)
            db.commit()
            db.refresh(farmer_user)

            farmer_profile = Farmer(
                user_id=farmer_user.id,
                national_id="1198570023412091",
                preferred_language="rw",
                cooperative_name="KOABIKI",
                is_phone_verified=True,
            )
            db.add(farmer_profile)
            db.commit()
            db.refresh(farmer_profile)

            # Seed primary location for farmer
            location = FarmerLocation(
                farmer_id=farmer_profile.id,
                province="Northern Province",
                district="Musanze",
                sector="Muhoza",
                cell="Mpenge",
                village="Gasharu",
                latitude=-1.4998,
                longitude=29.6349,
                is_primary=True,
            )
            db.add(location)
            db.commit()
            logger.info("Seeded sample Farmer: Jeanne Mukamana with primary location in Musanze/Muhoza.")

        logger.info("Database initialization and seed completed successfully.")

    except Exception as exc:
        db.rollback()
        logger.error(f"Error during database initialization: {exc}")
        raise exc
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    init_database()
