"""Health check Pydantic schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str = "1.0.0"
    database: str = "unknown"