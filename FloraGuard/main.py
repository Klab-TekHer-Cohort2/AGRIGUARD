
from fastapi import FastAPI

from app.api.alerts import router as alerts_router
from app.api.reports import router as reports_router
from app.api.risk import router as risk_router

app = FastAPI(
    title="FloraGuard API",
    description="Backend and community outbreak risk prediction system for flower growers.",
    version="1.0.0"
)

app.include_router(reports_router)
app.include_router(risk_router)
app.include_router(alerts_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to FloraGuard!",
        "status": "Backend is running",
        "project": "FloraGuard"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "FloraGuard Backend"
    }
