"""Computer-vision abstraction (section 6).

AgriGuard's crop-image analysis is wrapped behind a single ``VisionClassifier``
contract so the rest of the pipeline is agnostic to the underlying provider.

IMPORTANT — honesty (section 6 / section 27):
    We do NOT have a production-trained pest-detection model. This module ships
    TWO backends:

    1. ``SimulatedVisionClassifier`` — a deterministic, filename/pattern-based
       predictor. It is clearly labelled ``source = "simulated-demo"``. The same
       image identifier always maps to the same hint, so demos are reproducible.
       This is NOT real computer vision.

    2. ``PlantVillageCNNClassifier`` — an abstraction that shows exactly how a
       REAL trained CNN (e.g. a torchvision transfer-learning model trained on
       the public PlantVillage dataset, ~38 crop-disease classes) would plug in.
       It performs real image preprocessing (PIL resize/normalise) and, if torch
       + torchvision + a weights file are provided, runs a real forward pass and
       maps PlantVille labels onto AgriGuard problem ids. Without a weights file
       it raises a clear "not available" error — it never fakes a prediction.

    ``get_vision_classifier(mode=...)`` selects the backend. The default is the
    simulated classifier so the demo always runs; the notebook documents the
    real path and what would be needed to enable it (dataset, training, weights).
"""

import re
from typing import Dict, Optional

from ai.src import knowledge

# Optional deep-learning stack for the REAL path.
try:
    from PIL import Image  # noqa: F401
    PIL_AVAILABLE = True
except Exception:  # pragma: no cover
    PIL_AVAILABLE = False

try:
    import torch  # noqa: F401
    import torchvision  # noqa: F401
    TORCH_AVAILABLE = True
except Exception:  # pragma: no cover
    TORCH_AVAILABLE = False


# ── Simulated (deterministic) vision classifier ──────────────────────────────
# Filename -> problem-id patterns. Same input always yields the same hint.
DEMO_IMAGE_PATTERNS = [
    ("armyworm", "fall-armyworm"),
    ("maize.*leav|leav.*maize|maize-damage", "fall-armyworm"),
    ("mosaic", "cassava-mosaic-disease"),
    ("blight", "late-blight"),
    ("rust", "bean-rust"),
    (r"leaf.?spot", "gray-leaf-spot"),
    ("wilt", "bacterial-wilt"),
    ("aphid", "aphids"),
    ("yellow", "nitrogen-deficiency"),
    ("drought|dry", "drought-stress"),
    ("mealybug", "cassava-mealybug"),
    ("streak", "maize-streak-virus"),
    ("whitefly", "whitefly"),
    ("borer", "stalk-borer"),
]
_DEMO_COMPILED = [(re.compile(pat, re.IGNORECASE), pid) for pat, pid in DEMO_IMAGE_PATTERNS]


def _image_key(image) -> str:
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


class SimulatedVisionClassifier:
    """Deterministic, dependency-free 'vision' classifier (SIMULATED DEMO)."""

    name = "simulated"
    source = "simulated-demo"  # clearly labelled — NOT real CV

    def predict(self, image=None, crop_id: str = None, description: str = None) -> Dict:
        key = _image_key(image)
        matched = None

        for pattern, problem_id in _DEMO_COMPILED:
            if pattern.search(key):
                problem = knowledge.get_problem_by_id(problem_id)
                if problem and (
                    not crop_id or crop_id == "unknown" or crop_id in problem["affected_crops"]
                ):
                    matched = problem
                    break

        if not matched and crop_id and crop_id != "unknown":
            # Fallback: strongest keyword overlap with this crop's problems.
            text = (description or "").lower()
            best_score, matched = 0, None
            for p in knowledge.get_problems_by_crop(crop_id):
                score = sum(1 for kw in p["keywords"] if kw.lower() in text)
                if score > best_score:
                    best_score, matched = score, p

        if not matched:
            return {
                "text": "", "severity": None, "problem_hint": None,
                "confidence": 0.4, "source": self.source,
            }

        return {
            "text": matched["name_en"],
            "severity": matched.get("severity_example") or "Moderate",
            "problem_hint": matched["id"],
            "confidence": matched["confidence"],
            "source": self.source,
        }


# ── Real CNN classifier abstraction (PlantVillage-style) ─────────────────────
# Mapping from a subset of public PlantVillage label names to AgriGuard problem
# ids. A real deployment would train on (or fine-tune to) Rwandan field images
# and supply a complete label map + weights file.
PLANTVILLE_LABEL_MAP = {
    "Corn___fall_armyworm": "fall-armyworm",
    "Corn___leaf_blight": "late-blight",
    "Corn___common_rust": "bean-rust",
    "Corn___gray_leaf_spot": "gray-leaf-spot",
    "Cassava___mosaic": "cassava-mosaic-disease",
    "Cassava___brown_streak": "cassava-brown-streak",
    "Potato___late_blight": "late-blight",
    "Potato___early_blight": "early-blight",
    "Tomato___late_blight": "late-blight",
    "Tomato___early_blight": "early-blight",
    "Tomato___bacterial_spot": "bacterial-wilt",
    "Tomato___yellow_leaf_curl_virus": "whitefly",
}


class PlantVillageCNNClassifier:
    """Abstraction for a REAL trained CNN (transfer learning on PlantVillage).

    This class performs REAL image preprocessing and, when torch + torchvision +
    a weights file are supplied, a REAL forward pass. It deliberately does NOT
    ship weights (we have no production model), so by default it raises a clear
    error instead of fabricating predictions.

    To enable the real path:
        1. Train (or obtain) a CNN on the public PlantVillage dataset (or, better,
           on Rwandan field images) and export weights to ``weights_path``.
        2. Supply ``class_names`` in the same order as the model's output logits.
        3. Instantiate with ``weights_path`` and call ``load()`` before ``predict``.
    """

    name = "real-cnn"
    source = "real-model"

    def __init__(self, weights_path: Optional[str] = None, class_names: Optional[list] = None,
                 image_size: int = 224):
        self.weights_path = weights_path
        self.class_names = class_names or list(PLANTVILLE_LABEL_MAP.keys())
        self.image_size = image_size
        self.model = None

    def load(self):
        """Load the trained CNN weights. Requires torch + torchvision + a file."""
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "torch/torchvision not installed — cannot load a real CNN model"
            )
        if not self.weights_path:
            raise RuntimeError(
                "No weights_path provided. The real CNN is NOT available — use the "
                "simulated classifier for demos, or supply a trained weights file."
            )
        # Example wiring (kept generic; adapt to the exact trained architecture):
        # self.model = torchvision.models.resnet18(weights=None)
        # self.model.fc = torch.nn.Linear(self.model.fc.in_features, len(self.class_names))
        # state = torch.load(self.weights_path, map_location="cpu")
        # self.model.load_state_dict(state)
        # self.model.eval()
        raise NotImplementedError(
            "Real CNN loading is a template. Supply a trained model + implement the "
            "architecture wiring for your trained weights. See class docstring."
        )

    def _preprocess(self, image) -> "torch.Tensor":
        """Real preprocessing: PIL load -> resize -> normalise -> tensor."""
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow not installed")
        if isinstance(image, (bytes, bytearray)):
            import io
            img = Image.open(io.BytesIO(image)).convert("RGB")
        elif isinstance(image, str) and not image.startswith("http"):
            img = Image.open(image).convert("RGB")
        else:
            raise ValueError("Real path expects an image file path or raw bytes, not a demo filename")
        from torchvision import transforms
        transform = transforms.Compose([
            transforms.Resize((self.image_size, self.image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        return transform(img).unsqueeze(0)

    def predict(self, image=None, crop_id: str = None, description: str = None) -> Dict:
        if self.model is None:
            raise RuntimeError(
                "Real CNN not loaded. Call load() with a trained weights file, or "
                "use get_vision_classifier(mode='simulated') for the demo path."
            )
        tensor = self._preprocess(image)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0]
        best_idx = int(probs.argmax())
        label = self.class_names[best_idx]
        confidence = float(probs[best_idx])
        problem_id = PLANTVILLE_LABEL_MAP.get(label)
        problem = knowledge.get_problem_by_id(problem_id) if problem_id else None

        if not problem:
            return {
                "text": label, "severity": None, "problem_hint": None,
                "confidence": confidence, "source": self.source,
            }
        return {
            "text": problem["name_en"],
            "severity": problem.get("severity_example") or "Moderate",
            "problem_hint": problem["id"],
            "confidence": confidence,
            "source": self.source,
        }


# ── Backend selection ────────────────────────────────────────────────────────
def get_vision_classifier(mode: str = "simulated", **kwargs) -> object:
    """Select the vision backend.

    mode:
        "simulated" (default) -> SimulatedVisionClassifier  (always works)
        "real"               -> PlantVillageCNNClassifier  (needs torch + weights)
    """
    if mode == "real":
        return PlantVillageCNNClassifier(**kwargs)
    return SimulatedVisionClassifier()


def analyse_image(image=None, crop_id: str = None, description: str = None,
                  mode: str = "simulated", **kwargs) -> Dict:
    """Run the selected vision backend and normalise the output contract."""
    clf = get_vision_classifier(mode=mode, **kwargs)
    result = clf.predict(image=image, crop_id=crop_id, description=description)
    return {
        "text": result.get("text", "") or "",
        "severity": result.get("severity") or None,
        "problem_hint": result.get("problem_hint") or None,
        "confidence": result["confidence"] if isinstance(result.get("confidence"), (int, float)) else 0.5,
        "source": result.get("source", "simulated-demo"),
    }
