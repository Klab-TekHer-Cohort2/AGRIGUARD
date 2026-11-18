"""Image Analysis Service — abstraction layer for computer vision.

The cropAnalysisService NEVER calls a vision API directly. It calls this
module, which selects the right adapter based on AI_MODE:

    AI_MODE=mock   → deterministicMockAdapter   (always works, no API key)
    AI_MODE=openai → openaiVisionAdapter        (requires OPENAI_API_KEY)

Both adapters return the SAME contract:
    {"text", "severity", "problemHint", "confidence"}

The mock adapter is deterministic — given the same image identifier it always
returns the same hint. This keeps demos reproducible and tests stable.

To add a new real provider (e.g. PlantVillage, Google Vision, a custom CNN):
    1. Create app/services/adapters/<provider>_adapter.py exporting an
       analyse_image() coroutine.
    2. Add a branch in select_adapter() below.
No other file needs to change.

Mirrors ``src/services/imageAnalysisService.js``.
"""

import os
import logging

from app.config import settings
from app.services.adapters.deterministic_mock_adapter import deterministic_mock_adapter

logger = logging.getLogger("agriguard.image_analysis")


def select_adapter():
    """Choose the vision adapter based on AI_MODE and key availability."""
    if settings.mode == "openai":
        try:
            from app.services.adapters.openai_vision_adapter import openai_vision_adapter
        except Exception:  # pragma: no cover - adapter missing or deps unavailable
            logger.warning("[imageAnalysis] AI_MODE=openai but adapter unavailable. Falling back to mock.")
            return deterministic_mock_adapter
        if not os.getenv("OPENAI_API_KEY"):
            logger.warning("[imageAnalysis] AI_MODE=openai but OPENAI_API_KEY not set. Falling back to mock.")
            return deterministic_mock_adapter
        return openai_vision_adapter
    # mock (default)
    return deterministic_mock_adapter


class ImageAnalysisService:
    """Thin wrapper around the selected vision adapter that normalises output."""

    async def analyse_image(self, image=None, crop_id=None, description=None):
        adapter = select_adapter()
        result = await adapter.analyse_image(image=image, crop_id=crop_id, description=description)
        # Normalise: ensure every adapter returns all four fields.
        return {
            "text": result.get("text", "") or "",
            "severity": result.get("severity") or None,
            "problemHint": result.get("problemHint") or None,
            "confidence": result["confidence"] if isinstance(result.get("confidence"), (int, float)) else 0.5,
        }


# Module-level singleton.
image_analysis_service = ImageAnalysisService()
