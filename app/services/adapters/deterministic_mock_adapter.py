"""Deterministic Mock Vision Adapter.

Returns the SAME output for the SAME input — no randomness. This is the
prototype/demo fallback. The same image identifier always maps to the same
hint, so the rest of the pipeline stays deterministic.

The "vision" output here is derived from the image identifier (filename, hash,
or supplied test key) plus the crop context. In a real deployment this module
is replaced by a real adapter — nothing else changes.

Demo scenarios are encoded as explicit filename patterns so the hackathon demo
can use e.g. ``"maize-armyworm.jpg"`` and get a reproducible Fall Armyworm hint
without randomness.

Mirrors ``src/services/adapters/deterministicMockAdapter.js``.
"""

import re

from app.data import knowledge_base as kb

# Filename → problem hint mapping (the "demo tape"). Each rule is a compiled
# regex (case-insensitive) and a target problem id. The image parameter can be a
# filename, URL, base64 string, or test key.
DEMO_IMAGE_MAP = [
    {"match": re.compile(r"armyworm", re.IGNORECASE), "problemId": "fall-armyworm"},
    {"match": re.compile(r"maize.*leav|leav.*maize|maize-damage", re.IGNORECASE), "problemId": "fall-armyworm"},
    {"match": re.compile(r"mosaic", re.IGNORECASE), "problemId": "cassava-mosaic-disease"},
    {"match": re.compile(r"blight", re.IGNORECASE), "problemId": "late-blight"},
    {"match": re.compile(r"rust", re.IGNORECASE), "problemId": "bean-rust"},
    {"match": re.compile(r"leaf.?spot", re.IGNORECASE), "problemId": "gray-leaf-spot"},
    {"match": re.compile(r"wilt", re.IGNORECASE), "problemId": "bacterial-wilt"},
    {"match": re.compile(r"aphid", re.IGNORECASE), "problemId": "aphids"},
    {"match": re.compile(r"yellow", re.IGNORECASE), "problemId": "nitrogen-deficiency"},
    {"match": re.compile(r"drought|dry", re.IGNORECASE), "problemId": "drought-stress"},
    {"match": re.compile(r"mealybug", re.IGNORECASE), "problemId": "cassava-mealybug"},
    {"match": re.compile(r"streak", re.IGNORECASE), "problemId": "maize-streak-virus"},
    {"match": re.compile(r"whitefly", re.IGNORECASE), "problemId": "whitefly"},
    {"match": re.compile(r"borer", re.IGNORECASE), "problemId": "stalk-borer"},
]


def _image_key(image):
    """Normalise the image argument to a string key for pattern matching."""
    if not image:
        return ""
    if isinstance(image, str):
        return image
    if isinstance(image, (bytes, bytearray)):
        try:
            return image.decode("utf-8", errors="ignore")[:200]
        except Exception:
            return str(image)
    return str(image)


class DeterministicMockAdapter:
    """Deterministic, dependency-free vision adapter."""

    async def analyse_image(self, image=None, crop_id=None, description=None):
        key = _image_key(image)

        # 1. Try explicit demo mapping by filename pattern.
        matched_problem = None
        for rule in DEMO_IMAGE_MAP:
            if rule["match"].search(key):
                problem = kb.get_problem_by_id(rule["problemId"])
                if problem and (
                    not crop_id
                    or crop_id == "unknown"
                    or crop_id in problem["affectedCrops"]
                ):
                    matched_problem = problem
                    break

        # 2. If no explicit match, fall back to the description's strongest
        #    keyword intersection with this crop's problems — deterministic
        #    given the input.
        if not matched_problem and crop_id and crop_id != "unknown":
            candidates = kb.get_problems_by_crop(crop_id)
            text = (description or "").lower()
            best_score = 0
            for p in candidates:
                score = sum(1 for kw in p["keywords"] if kw.lower() in text)
                if score > best_score:
                    best_score = score
                    matched_problem = p

        # 3. No match → unknown hint, low confidence.
        if not matched_problem:
            return {
                "text": "",
                "severity": None,
                "problemHint": None,
                "confidence": 0.4,
            }

        return {
            "text": matched_problem["name"]["en"],
            "severity": matched_problem.get("severityExample") or "Moderate",
            "problemHint": matched_problem["id"],
            "confidence": matched_problem.get("confidence") or 0.7,
        }


# Module-level singleton.
deterministic_mock_adapter = DeterministicMockAdapter()
