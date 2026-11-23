"""AI integration service for smartphone image analysis.

This module provides a configurable interface for the computer vision model.
Member 1 is responsible for implementing the actual model.

The interface is:
    predict_image(image_path: str) -> Optional[dict]

The returned dict should contain:
    - problem_type: str
    - confidence: float (0.0 - 1.0)
    - description: Optional[str]

If the model is unavailable, predict_image returns None and the system
handles the failure gracefully without inventing predictions.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any, Callable, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Adapter for the computer vision model integration."""

    def __init__(self, model_path: str = "") -> None:
        self._model_path = model_path
        self._predict_fn: Optional[Callable[[str], Optional[dict]]] = None
        self._available = False
        self._error: Optional[str] = None

        if model_path:
            self._load_model(model_path)

    def _load_model(self, model_path: str) -> None:
        """Dynamically import the prediction function.

        Expected format: "package.module:function"
        """
        try:
            module_path, _, func_name = model_path.partition(":")
            if not func_name:
                func_name = "predict_image"
            module = importlib.import_module(module_path)
            self._predict_fn = getattr(module, func_name)
            self._available = True
            logger.info("AI model loaded from %s", model_path)
        except Exception as exc:
            self._available = False
            self._error = str(exc)
            logger.warning("AI model unavailable: %s", exc)

    @property
    def available(self) -> bool:
        """Whether the AI model is currently available."""
        return self._available

    @property
    def error(self) -> Optional[str]:
        """Last error message if the model failed to load."""
        return self._error

    async def predict_image(self, image_path: str) -> Optional[dict]:
        """Run prediction on an image.

        Returns a dict with problem_type, confidence, and optional description,
        or None if the model is unavailable.
        """
        if not self._available or self._predict_fn is None:
            logger.warning("AI model not available; skipping prediction")
            return None

        try:
            result = self._predict_fn(image_path)
            return result
        except Exception as exc:
            logger.error("AI prediction failed: %s", exc)
            return None

    def get_status(self) -> dict:
        """Return status information for health checks."""
        return {
            "available": self._available,
            "model_path": self._model_path,
            "error": self._error,
        }


# Singleton instance configured from settings
ai_service = AIService(model_path=settings.AI_MODEL_PATH)