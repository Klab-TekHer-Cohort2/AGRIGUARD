"""OpenAI GPT-4o Vision Adapter (REAL mode).

Calls the OpenAI Chat Completions API with an image attachment and a structured
prompt, returning the same contract as the mock adapter:

    {"text", "severity", "problemHint", "confidence"}

Requires:
    - OPENAI_API_KEY in env
    - httpx (a dependency)
    - AI_MODE=openai

The prompt is engineered to return STRICT JSON so the rest of the AgriGuard
pipeline can parse it deterministically. If the model returns something
unparseable, we degrade to an "unknown" hint rather than crashing.

SECURITY: the API key is read from env at call time and never logged.

Mirrors ``src/services/adapters/openaiVisionAdapter.js`` (which used axios;
this version uses httpx for async calls).
"""

import json
import os

import httpx

OPENAI_URL = os.getenv("OPENAI_URL", "https://api.openai.com/v1/chat/completions")
OPENAI_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")

PROMPT_EN = (
    "You are an agricultural pest and disease identification assistant for Rwandan smallholder farmers.\n"
    "Analyse this crop image and return ONLY a JSON object (no markdown, no commentary) with this exact schema:\n"
    "{\n"
    '  "text": "short English name of the suspected problem",\n'
    '  "severity": "Low" | "Moderate" | "High" | "Critical",\n'
    '  "problemHint": "the problem id from this list if you can match it, else null",\n'
    '  "confidence": 0.0 to 1.0\n'
    "}\n"
    "Problem ids to consider: fall-armyworm, stalk-borer, bean-fly, aphids, whitefly, cassava-mealybug,\n"
    "maize-streak-virus, gray-leaf-spot, angular-leaf-spot, late-blight, early-blight,\n"
    "cassava-mosaic-disease, bacterial-wilt, nitrogen-deficiency, potassium-deficiency,\n"
    "phosphorus-deficiency, magnesium-deficiency, zinc-deficiency, drought-stress, waterlogging, frost-damage.\n"
    'If you cannot confidently identify the problem, return '
    '{"text":"","severity":null,"problemHint":null,"confidence":0.3}.'
)


def _to_image_payload(image):
    """Convert the image argument to an OpenAI image_url payload, or None."""
    if not image:
        return None
    if isinstance(image, str):
        if image.startswith("http"):
            return {"url": image}  # Already a URL → pass as URL.
        if image.startswith("data:image"):
            return {"url": image}  # Already a base64 data URL.
        return {"url": f"data:image/jpeg;base64,{image}"}  # Raw base64 string.
    if isinstance(image, (bytes, bytearray)):
        import base64
        return {"url": f"data:image/jpeg;base64,{base64.b64encode(image).decode('ascii')}"}
    return None


class OpenAIVisionAdapter:
    """Real vision adapter calling the OpenAI Chat Completions API."""

    async def analyse_image(self, image=None, crop_id=None, description=None):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set — cannot use openai vision adapter")

        image_payload = _to_image_payload(image)
        if not image_payload:
            # No usable image — return unknown hint instead of failing.
            return {"text": "", "severity": None, "problemHint": None, "confidence": 0.4}

        user_text = f"Crop context: {crop_id or 'unknown'}. Farmer description: {description or 'none'}."
        body = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": PROMPT_EN},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": image_payload},
                    ],
                },
            ],
            "max_tokens": 300,
            "temperature": 0,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                OPENAI_URL,
                json=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        raw = (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
        try:
            # Strip any accidental markdown fences.
            clean = raw.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean)
        except (ValueError, AttributeError):
            # Model returned non-JSON → degrade to unknown.
            return {"text": "", "severity": None, "problemHint": None, "confidence": 0.4}

        return {
            "text": parsed.get("text", ""),
            "severity": parsed.get("severity"),
            "problemHint": parsed.get("problemHint"),
            "confidence": parsed["confidence"] if isinstance(parsed.get("confidence"), (int, float)) else 0.5,
        }


# Module-level singleton.
openai_vision_adapter = OpenAIVisionAdapter()
