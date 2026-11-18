# AgriGuard — AI & Data Layer

AI-Powered Pest Detection and Community Outbreak Early Warning System for Rwandan Smallholder Farmers.

This repository contains the **AI and Data layer** (Person 2's responsibility). It is a standalone **Python / FastAPI** service that provides crop problem analysis, an agricultural knowledge base, a RAG-powered assistant, community outbreak detection, and multilingual (English/Kinyarwanda) support.

> The AI and data work in this repo is done in **Python** (FastAPI). It exposes the same HTTP API and JSON contracts the backend and UI teammates already consume, so their integration is unaffected by the language choice. Real machine-learning code (scikit-learn, PyTorch, Hugging Face, LangChain, etc.) can be added on top of the adapter layer without touching the API.

## Quick start

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) configure environment
cp .env.example .env

# 4. Run the server (mock mode — no API keys needed)
uvicorn app.main:app --port 5000
# → http://localhost:5000  (interactive docs at /docs)

# 5. Run tests
pytest
```

The prototype runs fully in **mock mode** with zero external API keys. To use real OpenAI vision/text, set `AI_MODE=openai` and `OPENAI_API_KEY` in `.env`.

## Run the demo

```bash
# Full end-to-end demo (one request):
curl http://localhost:5000/api/ai/demo
```

Or start the server and open `http://localhost:5000/api/ai/demo` in a browser.

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/ai/analyse-report` | Analyse a single crop report (smartphone flow) |
| POST | `/api/ai/ask` | Ask AgriGuard a free-form agricultural question |
| POST | `/api/ai/community-risk` | Community outbreak risk from a set of reports |
| POST | `/api/ai/outbreak-detection` | Full outbreak detection + alertable farmers within 5 km |
| POST | `/api/ai/ussd-response` | USSD channel — same AI, short plain-text output |
| GET  | `/api/ai/demo` | Full hackathon demo scenario |
| GET  | `/health` | Service health + mode |

These endpoints and their JSON request/response contracts are identical to the previous Node.js/Express implementation, so the backend teammate's client code does not need to change.

Full request/response contracts: see [`docs/AI_DOCUMENTATION.md`](docs/AI_DOCUMENTATION.md).

## Google Colab — AI & Data experiments

The `ai/` directory is the **Google Colab runnable ML/data component** for this
project. It contains:
- Real scikit-learn TF-IDF + Logistic Regression crop-problem classifier
- Sentence-transformers + FAISS semantic RAG (keyword fallback when not installed)
- Computer-vision abstraction (simulated demo path clearly labelled; real CNN template)
- Community outbreak detection with a transparent 0–100 risk score
- 5 km Haversine alert eligibility
- Multilingual EN/RW support
- Prototype CSV datasets
- 36 pytest tests
- A complete demo notebook with 16 sections + 4 end-to-end scenarios

**Open the demo in Google Colab:**

```text
ai/notebooks/agriguard_ai_demo.ipynb
```

**Quick install:**

```bash
pip install pandas numpy scikit-learn matplotlib Pillow python-dotenv
# Optional semantic RAG:
pip install sentence-transformers faiss-cpu
```

**Run AI tests:**

```bash
pytest ai/tests/ -q        # 36 tests
```

See [`ai/README.md`](ai/README.md) for the full Colab setup guide, integration
instructions for Person 1 (frontend) and Person 3 (backend/USSD), real-vs-prototype
data honesty table, and what remains to be integrated.

---

## Project structure

```
AGRIGUARD/
├── ai/                               # Google Colab ML/data component (Person 2)
│   ├── notebooks/
│   │   └── agriguard_ai_demo.ipynb   ← Open this in Google Colab
│   ├── src/
│   │   ├── models.py                 # Dataclass result contracts
│   │   ├── confidence.py             # Confidence tier (configurable)
│   │   ├── severity.py               # Severity (independent of confidence)
│   │   ├── alert_logic.py            # Escalation + Haversine + 5 km alerts
│   │   ├── multilingual.py           # EN/RW detection + messages
│   │   ├── knowledge.py              # CSV loader + lookups
│   │   ├── classification.py         # sklearn TF-IDF + LogReg + keyword fallback
│   │   ├── rag.py                    # sentence-transformers+FAISS + keyword fallback
│   │   ├── vision.py                 # CV abstraction (simulated + real CNN template)
│   │   ├── recommendations.py        # Localised recommendation generator
│   │   ├── crop_analysis.py          # Main orchestrator: analyze_report + ussd_format
│   │   ├── assistant.py              # answer_farmer_question (RAG-grounded)
│   │   └── outbreak_detection.py     # detect_outbreak + transparent risk score
│   ├── data/
│   │   ├── build_csvs.py             # Regenerate CSVs from app/data/
│   │   ├── crops.csv                 # 5 crops
│   │   ├── crop_problems.csv         # 21 problems
│   │   ├── agricultural_knowledge.csv # 31 RAG articles
│   │   ├── demo_reports.csv          # 16 PROTOTYPE reports
│   │   └── demo_farmers.csv          # 9 PROTOTYPE farmers
│   ├── tests/                        # 36 pytest tests
│   └── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI app entry point
│   ├── config.py                      # All configurable thresholds (env-driven)
│   ├── data/
│   │   ├── knowledge_base/
│   │   │   ├── __init__.py            # Lookup + RAG article flattening
│   │   │   ├── crops.py               # 5 crops (maize, beans, cassava, potato, tomato)
│   │   │   └── problems.py            # 21 problems across 4 categories
│   │   └── prototype_dataset.py      # Demo farmers, reports, communities, scenarios
│   ├── routes/
│   │   └── ai_routes.py               # All /api/ai endpoints
│   ├── services/
│   │   ├── crop_analysis_service.py   # Main AI entry point → CropAnalysisResult
│   │   ├── image_analysis_service.py  # Vision adapter selector (mock/openai)
│   │   ├── adapters/
│   │   │   ├── deterministic_mock_adapter.py  # Mock vision (deterministic)
│   │   │   ├── openai_vision_adapter.py       # Real GPT-4o vision
│   │   │   └── openai_text_adapter.py         # Real GPT-4o-mini text
│   │   ├── rag_service.py            # RAG retrieval (keyword prototype)
│   │   ├── ai_assistant_service.py    # Ask AgriGuard assistant
│   │   ├── outbreak_detection_service.py # Community risk + 5km alert
│   │   ├── escalation_service.py     # Agronomist escalation logic
│   │   ├── language_service.py       # EN/RW detection + localisation
│   │   └── ussd_response_formatter.py # USSD short-text formatter
│   ├── utils/
│   │   └── geo_utils.py              # Haversine distance + radius queries
│   └── middleware/
│       └── error_handler.py
├── tests/                            # FastAPI integration test suite (69 tests)
├── docs/
│   └── AI_DOCUMENTATION.md           # Full architecture + API contracts
├── requirements.txt                  # FastAPI service deps
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

## Testing

```bash
pytest                  # FastAPI service tests (69 tests)
pytest ai/tests/ -q     # AI/ML component tests (36 tests)
pytest -q               # all tests together (105 tests)
pytest --cov=app        # coverage for the FastAPI service (needs pytest-cov)
```

**FastAPI service tests** (`tests/`) cover: confidence thresholds, severity independence,
agronomist escalation, crop analysis (Fall Armyworm + unknown), data quality, outbreak
detection (cluster + isolated), 5 km radius filtering, Haversine distance, language
detection, RAG retrieval, Ask AgriGuard (EN/RW/no-retrieval), USSD formatting, and all
API routes.

**AI/ML component tests** (`ai/tests/`) cover: confidence boundaries, escalation rules,
Haversine + 5 km eligibility, language detection, outbreak detection (cluster + isolated
+ empty), scikit-learn classifier training + evaluation, keyword fallback, and
`analyze_report` end-to-end.

## Key design decisions

- **One AI layer, multiple channels.** Smartphone, USSD, and IVR all call the same `crop_analysis_service.analyse_crop_report()`. Only the output formatting differs.
- **Mock-first.** The prototype runs deterministically with no API keys. Swapping to real OpenAI only requires an env var.
- **Adapter pattern.** Vision/text providers are pluggable adapters behind a single contract. Add a new ML provider (a custom CNN, PlantVillage model, Google Vision, etc.) by writing one adapter file and adding a branch in `select_adapter()` — nothing else changes. This is the natural integration point for Python-native ML libraries.
- **Responsible AI.** High/critical severity always escalates to an agronomist, even at high confidence. Unknown problems escalate. The AI never claims to replace agronomists.
- **Prototype honesty.** All outbreak results carry `prototype: true` and a disclaimer. Simulated data is explicitly labelled.
