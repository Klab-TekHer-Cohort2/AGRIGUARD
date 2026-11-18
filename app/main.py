"""AgriGuard AI Backend — FastAPI application entry point.

Replaces ``src/server.js``. Exposes the same endpoints and JSON contracts on
the same default port (5000), so the backend and UI teammates are unaffected by
the language change.

Run with::

    uvicorn app.main:app --port 5000
or::
    python -m app.main
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.ai_routes import router as ai_router
from app.middleware.error_handler import unhandled_exception_handler

app = FastAPI(
    title="AgriGuard AI Service",
    version="1.0.0",
    description="AgriGuard — AI-Powered Pest Detection and Community Outbreak Early Warning System (AI & Data layer).",
)

# ── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin] if settings.cors_origin != "*" else ["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False,
)


# ── Health check ────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def health():
    return {
        "status": "ok",
        "service": "AgriGuard AI Service",
        "version": "1.0.0",
        "mode": settings.mode,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


# ── Routes ──────────────────────────────────────────────────────────────────
app.include_router(ai_router)

# ── Error handling ──────────────────────────────────────────────────────────
app.add_exception_handler(Exception, unhandled_exception_handler)


def main():
    """Run the server with uvicorn when invoked directly (``python -m app.main``)."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    print(f"\n🌱 AgriGuard AI Service starting on port {settings.port}")
    print(f"   Mode : {settings.mode}")
    print(f"   Env  : development")
    print(f"   Health: http://localhost:{settings.port}/health\n")
    main()
