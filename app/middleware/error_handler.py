"""Centralized error handling for the FastAPI app.

Provides a handler for unhandled exceptions that returns the same JSON error
shape as the previous Express implementation:
    {"success": false, "error": <code>, "message": <message>}

Mirrors ``src/middleware/errorHandler.js``.
"""

import logging
import os

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("agriguard.error")


async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions → 500 with the AgriGuard error shape."""
    logger.error("[AgriGuard Error] %s", exc, exc_info=True)
    body = {
        "success": False,
        "error": "INTERNAL_ERROR",
        "message": str(exc) or "An unexpected error occurred",
    }
    if os.getenv("NODE_ENV") == "development":
        import traceback
        body["stack"] = traceback.format_exc()
    return JSONResponse(status_code=500, content=body)
