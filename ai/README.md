# AgriGuard — AI & Data Component (Person 2)

Python AI/ML layer for **AgriGuard** — an AI-powered pest detection and community
outbreak early-warning system for Rwandan smallholder farmers.

This component is **Google Colab runnable**. All AI and machine-learning logic
lives in pure Python modules under `ai/src/`. The FastAPI service in `app/`
calls these same modules, so there is one AI codebase shared between local
experiments (notebook) and the deployed API.

---

## 1. How to open and run in Google Colab

### Option A — Upload the repository

1. Go to [colab.research.google.com](https://colab.research.google.com).
2. **File → Upload notebook** → select `ai/notebooks/agriguard_ai_demo.ipynb`.
3. Upload the whole repository to Colab or mount Google Drive.
4. In the first code cell, make sure `REPO_ROOT` points to the repo root.
5. Click **Runtime → Run all**.

### Option B — Clone from GitHub (if the repo is on GitHub)

```python
# In a Colab code cell:
!git clone https://github.com/YOUR_ORG/AGRIGUARD.git
import sys
sys.path.insert(0, '/content/AGRIGUARD')
```

Then open `ai/notebooks/agriguard_ai_demo.ipynb`.

---

## 2. Required pip install commands

### Core (always needed — fast to install)

```bash
pip install pandas>=2.0 numpy>=1.24 scikit-learn>=1.3 matplotlib>=3.7 Pillow>=10.0 python-dotenv>=1.0
```

### Optional — real semantic RAG with embeddings

```bash
pip install sentence-transformers>=2.7 faiss-cpu>=1.7
```

The pipeline falls back to **keyword retrieval** automatically if these are not
installed — the demo always runs.

### Optional — real computer-vision CNN (not needed for the demo)

```bash
pip install torch torchvision
```

Only needed if you supply a trained CNN weights file (see `ai/src/vision.py`
`PlantVillageCNNClassifier`).

### Install everything at once (Colab cell 1 does this automatically)

```bash
pip install -r ai/requirements.txt
```

---

## 3. Project structure

```
ai/
├── notebooks/
│   └── agriguard_ai_demo.ipynb   ← Open this in Google Colab
│
├── src/
│   ├── __init__.py
│   ├── models.py          Dataclass result contracts (CropAnalysisResult, etc.)
│   ├── confidence.py      Confidence tier classification (configurable thresholds)
│   ├── severity.py        Severity assessment (independent of confidence)
│   ├── alert_logic.py     Escalation + Haversine distance + 5 km alert eligibility
│   ├── multilingual.py    EN/RW language detection + localised messages
│   ├── knowledge.py       CSV loader + lookup helpers (single data-access point)
│   ├── classification.py  sklearn TF-IDF+LogReg classifier + keyword fallback
│   ├── rag.py             sentence-transformers+FAISS retriever + keyword fallback
│   ├── vision.py          CV abstraction: SimulatedVisionClassifier + CNN template
│   ├── recommendations.py Localised recommendation generator
│   ├── crop_analysis.py   Main orchestrator: analyze_report + ussd_format
│   ├── assistant.py       answer_farmer_question (RAG-grounded, offline)
│   └── outbreak_detection.py  detect_outbreak + transparent risk score
│
├── data/
│   ├── build_csvs.py              Regenerate CSVs from app/data/ knowledge base
│   ├── crops.csv                  5 crops
│   ├── crop_problems.csv          21 problems (Pest/Disease/NutrientDeficiency/Environmental)
│   ├── agricultural_knowledge.csv 31 RAG knowledge articles
│   ├── demo_reports.csv           16 PROTOTYPE farmer reports
│   └── demo_farmers.csv            9 PROTOTYPE registered farmers
│
├── tests/
│   ├── test_confidence.py   Confidence tier boundary tests
│   ├── test_escalation.py   Agronomist escalation logic tests
│   ├── test_distance.py     Haversine + 5 km radius tests
│   ├── test_language.py     Language detection tests
│   ├── test_outbreak.py     Outbreak detection tests
│   └── test_classification.py  Keyword + sklearn classifier tests
│
├── requirements.txt
└── README.md                ← this file
```

---

## 4. How to test crop analysis

### In a notebook / Colab cell

```python
from ai.src.crop_analysis import analyze_report

result = analyze_report(
    crop="Maize",
    description="The leaves have holes and I can see small insects near the whorl.",
    image="maize-armyworm.jpg",   # demo filename → deterministic simulated hint
    language="en",
)
print(result.to_dict())
```

### Expected output (keyword or ML path)

```python
{
  "crop": "Maize",
  "crop_id": "maize",
  "category": "Pest",
  "possible_problem": "Fall Armyworm",
  "problem_id": "fall-armyworm",
  "confidence": 0.96,
  "confidence_level": "High",
  "severity": "Moderate",
  "recommendation": ["Inspect nearby maize plants ...", ...],
  "needs_agronomist": False,
  "escalation_reason": "none",
  "vision_source": "simulated-demo",   ← always clearly labelled
  "source": "keyword",                 ← or "ml" after train_classifier()
  ...
}
```

### Train the ML classifier first (optional but recommended)

```python
from ai.src import classification
eval_result = classification.train_classifier()
print(f"Accuracy: {eval_result['accuracy']:.3f}")
# Then analyze_report uses the ML model automatically.
```

---

## 5. How to test the RAG assistant

```python
from ai.src.assistant import answer_farmer_question

# English
ans = answer_farmer_question(
    "How do I protect my maize from Fall Armyworm?", language="en"
)
print(ans.answer)
print(f"Sources: {ans.sources}")

# Kinyarwanda (auto-detected)
ans_rw = answer_farmer_question(
    "Ibigori byanjye birimo gukangarwa n'udukoko, mbwira inama."
)
print(ans_rw.answer)
```

### Enable semantic embeddings (better retrieval quality)

```python
from ai.src import rag
# Install sentence-transformers + faiss-cpu first, then:
rag.build_embeddings_index()     # downloads all-MiniLM-L6-v2 (~90 MB, cached)
print(f"Retriever: {rag.retriever_method()}")  # "embeddings"
```

---

## 6. How to test outbreak detection

```python
from ai.src import knowledge
from ai.src.outbreak_detection import detect_outbreak

reports = knowledge.reports_as_dicts()
result = detect_outbreak(reports)

print(f"Risk level : {result.risk_level}")
print(f"Risk score : {result.risk_score}/100")
print(f"Problem    : {result.problem}")
print(f"Crop       : {result.crop}")
print(f"Area       : {result.affected_area}")
print(f"PROTOTYPE  : {result.is_prototype}")   # always True for demo data
```

---

## 7. How to test the 5 km alert logic

```python
from ai.src import knowledge
from ai.src.alert_logic import farmers_within_radius, calculate_distance_km
from ai.src.outbreak_detection import detect_outbreak

reports = knowledge.reports_as_dicts()
farmers = knowledge.farmers_as_dicts()

outbreak = detect_outbreak(reports)
centre = outbreak.affected_area_center       # {"lat": ..., "lng": ...}

alertable = farmers_within_radius(
    centre["lat"], centre["lng"], farmers, radius_km=5.0
)
for f in alertable:
    print(f"{f.farmer_id}  {f.name}  {f.distance_km:.2f} km")

# Individual distance check
d = calculate_distance_km(-1.479, 30.419, -1.56, 30.33)
print(f"Distance to Nyagatare: {d:.1f} km")  # > 5 km → not eligible
```

---

## 8. How Person 3 (backend / USSD / IVR) connects to the Python AI

### Option A — Call the FastAPI HTTP endpoints (recommended for production)

The `app/` FastAPI service exposes these endpoints that internally call the
`ai/src` modules:

| Endpoint | Description |
|----------|-------------|
| `POST /api/ai/analyse-report` | Crop report analysis (smartphone + USSD) |
| `POST /api/ai/ask` | Ask AgriGuard assistant |
| `POST /api/ai/community-risk` | Community risk from reports |
| `POST /api/ai/outbreak-detection` | Full outbreak + alertable farmers |
| `POST /api/ai/ussd-response` | USSD-formatted short response |

**Example (Person 3 backend calling the AI service):**

```python
import httpx

# Analyse a USSD report
response = httpx.post("http://localhost:5000/api/ai/ussd-response", json={
    "farmerId": "F003",
    "crop": "Maize",
    "problemDescription": "Holes in leaves, insects in the whorl",
    "location": "Kabarore",
    "language": "en",
})
data = response.json()
ussd_text = data["data"]["ussdResponse"]
# → Short plain text: "Possible problem: Fall Armyworm\nConfidence: 96%..."
```

### Option B — Import `ai/src` modules directly (same process, monorepo)

If Person 3's backend runs in the same Python process:

```python
from ai.src.crop_analysis import analyze_report, process_ussd_report

# USSD report
result = process_ussd_report(
    farmer_id="F003",
    crop="Maize",
    problem_description="Holes in leaves",
    location="Kabarore",
    language="en",
)
ussd_text = result["ussd_response"]
analysis  = result["analysis"]
```

### Community risk (from Person 3's report database)

```python
from ai.src.outbreak_detection import detect_outbreak
from ai.src.alert_logic import farmers_within_radius

# reports = your DB query result, converted to list of dicts with these keys:
#   problem_id, crop_id, category, confidence, severity,
#   latitude, longitude, community, timestamp
outbreak = detect_outbreak(reports)

if outbreak.alert_recommended:
    eligible = farmers_within_radius(
        outbreak.affected_area_center["lat"],
        outbreak.affected_area_center["lng"],
        farmers,          # list of {"id", "lat", "lng", "name", "community"}
        radius_km=5.0,
    )
    # Send SMS/USSD alert to each farmer in eligible
```

---

## 9. How Person 1 (smartphone frontend) consumes AI results

Person 1 calls the FastAPI service over HTTP. The JSON contract from
`POST /api/ai/analyse-report` is:

```json
{
  "success": true,
  "data": {
    "crop": "Maize",
    "cropId": "maize",
    "category": "Pest",
    "possibleProblem": "Fall Armyworm",
    "problemId": "fall-armyworm",
    "confidence": 0.96,
    "confidenceTier": "high",
    "confidenceLabel": "High",
    "severity": "Moderate",
    "recommendation": ["Inspect nearby maize plants ...", "..."],
    "recommendationText": "Inspect nearby maize plants ...",
    "needsAgronomist": false,
    "escalationReason": "none",
    "language": "en",
    "imageAnalysed": true,
    "disclaimer": "Prototype AI assessment — not a substitute for professional agronomist advice.",
    "timestamp": "2026-11-17T..."
  }
}
```

Key fields Person 1 should display:

| Field | UI usage |
|-------|----------|
| `possibleProblem` | Main problem card title |
| `confidence` + `confidenceLabel` | Confidence badge |
| `severity` | Severity colour chip (Low=green, Moderate=orange, High=red, Critical=dark red) |
| `recommendation` | Bulleted action list |
| `needsAgronomist` | Escalation banner (show when `true`) |
| `disclaimer` | Always display at the bottom of every AI result card |

---

## 10. What is simulated and what is based on real / public data

| Component | Status | Notes |
|-----------|--------|-------|
| TF-IDF + Logistic Regression classifier | **Real ML** (scikit-learn) | Trained on knowledge base, real `predict_proba` |
| RAG with sentence-transformers + FAISS | **Real ML** | `all-MiniLM-L6-v2`, real cosine similarity search |
| RAG keyword fallback | Deterministic heuristic | No ML; always available |
| Vision analysis (`SimulatedVisionClassifier`) | **Simulated demo** — clearly labelled `source="simulated-demo"` | Filename pattern matching, NOT real CV |
| Vision analysis (`PlantVillageCNNClassifier`) | **Real ML abstraction** — template only | Needs trained weights + torch; not shipped |
| Knowledge base (crops.csv, crop_problems.csv) | Prototype from public agricultural literature | FAO, RAB, CABI public summaries — not certified advice |
| Agricultural knowledge articles (RAG) | Prototype from same sources | Used for retrieval only |
| Demo farmer reports (demo_reports.csv) | **PROTOTYPE — NOT real data** | Simulated Kabarore cluster + isolated cases |
| Demo farmers (demo_farmers.csv) | **PROTOTYPE — NOT real data** | Approximate community centroids, not real people |
| Risk score algorithm | Transparent heuristic (0–100) | NOT a scientifically validated outbreak probability |

---

## 11. What remains to be integrated

| Item | Owner | Status |
|------|-------|--------|
| Real image dataset (PlantVillage or Rwandan field images) | Person 2 | Needs data collection + CNN training |
| Real USSD gateway integration | Person 3 | Backend glue only — AI contract is ready |
| Smartphone image upload → AI service | Person 1 | Send image bytes to `POST /api/ai/analyse-report` |
| Person 3 database → outbreak detection | Person 3 | Convert DB rows to report dicts, call `detect_outbreak` |
| OpenAI / Hugging Face LLM for real answer generation | Person 2 | Plug into `ai/src/assistant._load_llm_adapter()` |
| Kinyarwanda performance validation | Person 2 | Needs field testing with real farmers |
| GPS coordinates from mobile phones | Person 1 | Pass `location: {lat, lng, community}` to `analyse-report` |
| Production ML model retraining on real Rwandan data | Person 2 | Knowledge base expansion needed first |

---

## Run the pytest suite

```bash
# From the repository root:
pytest ai/tests/ -q
# Expected: 36 passed
```

---

## Model limitations (Section 27 — honesty)

- The prototype knowledge base is small and may not cover all Rwandan field
  conditions or crop varieties.
- Image classification is currently **simulated** — the vision `source` field
  always says `"simulated-demo"` so callers are never misled.
- Kinyarwanda support is keyword-based detection + template grounding — not a
  trained multilingual model. Performance must be validated with real farmers.
- The outbreak risk score (0–100) is a transparent **heuristic**, not a
  statistical probability model.
- All AI recommendations must be validated by a qualified agronomist before
  being used to make farm management decisions.
- The prototype data (Kabarore cluster etc.) is for demonstration only and does
  NOT represent a real current outbreak.
