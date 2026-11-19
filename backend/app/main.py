import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import check_database_connection
from app.core.neo4j_client import neo4j_client
from app.api.v1.auth import router as auth_router
from app.api.v1.farmers import router as farmers_router
from app.api.v1.locations import router as locations_router
from app.api.v1.crops import router as crops_router
from app.api.v1.reports import router as reports_router
from app.api.v1.ai import router as ai_router
from app.api.v1.agronomists import router as agronomists_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.outbreak import router as outbreak_router
from app.ussd import router as ussd_router
from app.ivr import router as ivr_router


class UploadStaticFiles(StaticFiles):
    def file_response(self, full_path, stat_result, scope, status_code=200):
        response = super().file_response(full_path, stat_result, scope, status_code)
        response.headers["Content-Disposition"] = "attachment"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)
logger = logging.getLogger("agriguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager:
    Handles startup (DB verify, Neo4j connect) and shutdown cleanups.
    """
    logger.info("Starting AgriGuard Backend Engine...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize Neo4j Graph Driver
    try:
        neo4j_client.connect()
    except Exception as exc:
        logger.warning(f"Neo4j startup notice: {exc}")

    # Initialize and seed relational database schema
    try:
        from app.core.init_db import init_database
        init_database()
    except Exception as exc:
        logger.error(f"Database schema initialization failed: {exc}")

    # Check Relational Database
    db_status = check_database_connection()
    logger.info(f"Relational Database Status: {db_status.get('status')}")

    yield

    # Clean shutdown
    logger.info("Shutting down AgriGuard Backend Engine...")
    neo4j_client.close()


app = FastAPI(
    title="AgriGuard API",
    description=(
        "AI-Powered Pest Detection and Community Outbreak Early Warning System "
        "for Rwandan Smallholder Farmers.\n\n"
        "Connects Farmers (USSD & IVR), Agronomists, Mobile/Web Apps, AI Detection, "
        "and Neo4j Knowledge Graph & Outbreak Propagation Engine."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) for Frontend and Mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads static directory for crop photo preview
app.mount("/uploads", UploadStaticFiles(directory=str(settings.upload_path)), name="uploads")

# Include API v1 Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(farmers_router, prefix=settings.API_V1_STR)
app.include_router(locations_router, prefix=settings.API_V1_STR)
app.include_router(crops_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(agronomists_router, prefix=settings.API_V1_STR)
app.include_router(organizations_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(outbreak_router, prefix=settings.API_V1_STR)

# Gateway-gated farmer channels (USSD & IVR) — authenticated by shared secret, not JWT
app.include_router(ussd_router, prefix=settings.API_V1_STR)
app.include_router(ivr_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root_endpoint():
    """Welcome endpoint providing basic API metadata."""
    return {
        "project": "AgriGuard",
        "description": "AI-Powered Pest Detection & Community Early Warning System",
        "country": "Rwanda",
        "documentation": "/docs",
        "api_v1": settings.API_V1_STR,
        "status": "online"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Unified health check verifying Relational DB, Neo4j Graph DB, and Core Services.
    """
    db_health = check_database_connection()
    neo4j_health = neo4j_client.check_connection()

    all_healthy = (db_health.get("status") == "connected")

    return {
        "status": "healthy" if all_healthy else "degraded",
        "environment": settings.ENVIRONMENT,
        "relational_database": db_health,
        "neo4j_graph_database": neo4j_health,
        "ai_service_endpoint": settings.AI_SERVICE_URL,
        "ai_mock_fallback_active": settings.AI_SERVICE_MOCK_FALLBACK
    }
