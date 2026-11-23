
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db

from app.api.alerts import router as alerts_router
from app.api.ivr import router as ivr_router
from app.api.map import router as map_router
from app.api.reports import router as reports_router
from app.api.risk import router as risk_router
from app.api.ussd import router as ussd_router

app = FastAPI(
    title="FloraGuard API",
    description="Backend and community outbreak risk prediction system for flower growers.",
    version="1.0.0"
)

app.include_router(reports_router)
app.include_router(risk_router)
app.include_router(alerts_router)
app.include_router(ussd_router)
app.include_router(ivr_router)
app.include_router(map_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to FloraGuard!",
        "status": "Backend is running",
        "project": "FloraGuard"
    }


from app.services.ai_service import ai_service

from sqlalchemy import text

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "unavailable"
    try:
        db.execute(text("SELECT 1"))
        db_status = "available"
    except Exception:
        db_status = "unavailable"

    overall = "healthy" if db_status == "available" else "degraded"
    status_code = 200 if db_status == "available" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall,
            "service": "FloraGuard Backend",
            "database": db_status,
            "ai_available": ai_service.available,
            "weather_configured": bool(settings.WEATHER_BASE_URL),
        },
    )
