# AgriGuard — UI Integration Guide (Person 1)

This guide tells Person 1 (UI developer) exactly how to connect the frontend
to both the **Backend API** (Person 3) and the **AI Service** (Person 2).

---

## Architecture overview

```
┌──────────────────────────────────┐
│         UI  (Person 1)           │
│  React / React Native / Flutter  │
└──────────┬───────────────────────┘
           │  HTTP + JWT
           ▼
┌──────────────────────────────────┐
│      Backend API  (Person 3)     │
│  FastAPI  —  port 8000           │
│  /api/v1/*                       │
│  SQLite / PostgreSQL + Neo4j     │
└──────────┬───────────────────────┘
           │  internal HTTP
           ▼
┌──────────────────────────────────┐
│      AI Service  (Person 2)      │
│  FastAPI  —  port 5000           │
│  /api/ai/*                       │
│  Python ML / RAG / Voice         │
└──────────────────────────────────┘
```

**The UI never calls the AI Service directly.**
It calls the Backend, which calls the AI Service internally.
One exception: for direct AI demos/prototyping you may call port 5000, but
in production all traffic goes through the Backend.

---

## Step 1 — Start the services locally

### AI Service (Person 2 — port 5000)

```bash
# From the repo root:
pip install -r requirements.txt
uvicorn app.main:app --port 5000 --reload
# → http://localhost:5000
# → http://localhost:5000/docs   (interactive API docs)
```

### Backend (Person 3 — port 8000)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # configure DB, JWT secret, AI service URL
python run.py                 # or: uvicorn app.main:app --port 8000 --reload
# → http://localhost:8000
# → http://localhost:8000/docs
```

### Configure the Backend to find the AI Service

In `backend/.env`:
```
AI_SERVICE_URL=http://localhost:5000/api/v1/predict
AI_SERVICE_MOCK_FALLBACK=True
```

---

## Step 2 — Authentication (every UI request needs a JWT token)

### Register a new farmer account

```
POST http://localhost:8000/api/v1/auth/register
Content-Type: application/json

{
  "phone_number": "+250788123456",
  "password": "securepassword",
  "full_name": "Mukamana Beatrice",
  "role": "FARMER",
  "preferred_language": "rw",
  "district": "Gatsibo"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "role": "FARMER",
  "user_id": 1,
  "phone_number": "+250788123456",
  "full_name": "Mukamana Beatrice"
}
```

### Login

```
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "phone_number": "+250788123456",
  "password": "securepassword"
}
```

### Use the token in every subsequent request

```
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

---

## Step 3 — Key API endpoints for the UI

All endpoints are under `http://localhost:8000/api/v1/`.
Interactive docs: `http://localhost:8000/docs`

### 3a. Farmer profile

```
GET  /farmers/profile              → get logged-in farmer's profile
PUT  /farmers/profile              → update name, language, cooperative
```

### 3b. Submit a crop report (the main farmer action)

```
POST /reports/
Authorization: Bearer <token>
Content-Type: application/json

{
  "crop_id": 1,
  "channel": "APP",
  "description": "Leaves have holes and small insects near the whorl",
  "symptoms": ["holes in leaves", "insects visible"],
  "severity": "MODERATE",
  "district": "Gatsibo",
  "sector": "Kabarore",
  "latitude": -1.479,
  "longitude": 30.419
}
```

**Response includes** the full report with AI analysis result:
```json
{
  "id": 42,
  "report_code": "AG0042",
  "ai_result": {
    "predicted_pest_en": "Fall Armyworm",
    "predicted_pest_rw": "Nkongwa",
    "confidence_score": 0.94,
    "detected_severity": "HIGH",
    "recommendations": ["Spray neem extract...", "Contact extension worker..."],
    "is_mock": false
  }
}
```

### 3c. Upload a crop photo (after submitting the report)

```
POST /reports/{report_id}/images
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image file>  (JPEG / PNG / WebP, max 10 MB)
```

The backend stores the image, calls the AI vision analysis automatically,
and updates the report's `ai_result`.

### 3d. Trigger AI analysis manually

```
POST /ai/analyze/{report_id}
Authorization: Bearer <token>
```

### 3e. Get AI result for a report

```
GET /ai/results/{report_id}
Authorization: Bearer <token>
```

**Response fields to display in the UI:**

| Field | Display as |
|-------|-----------|
| `predicted_pest_en` | Problem name (English) |
| `predicted_pest_rw` | Problem name (Kinyarwanda) |
| `confidence_score` | Confidence badge (0–1 → "High / Medium / Low") |
| `detected_severity` | Severity chip (LOW / MODERATE / HIGH / CRITICAL) |
| `recommendations` | Bulleted action list |
| `is_mock` | Show "Demo result" badge when `true` |

### 3f. My reports list

```
GET /reports/my-reports
GET /reports/my-reports?status_filter=PENDING&limit=20
Authorization: Bearer <token>
```

### 3g. Outbreak alerts (agronomist/admin dashboard)

```
GET /outbreak/alerts
GET /outbreak/alerts?district=Gatsibo&severity=HIGH
GET /outbreak/risk-score?district=Gatsibo
Authorization: Bearer <token>  (agronomist/admin role required)
```

### 3h. Dashboard stats (agronomist/admin)

```
GET /dashboard/
Authorization: Bearer <token>
```

---

## Step 4 — Calling the AI service directly (optional / demo only)

If you want to call the AI service directly from the UI for demos:

### Analyse a crop report

```
POST http://localhost:5000/api/ai/analyse-report
Content-Type: application/json

{
  "crop": "Maize",
  "description": "Holes in leaves, small insects near the whorl",
  "language": "en"
}
```

### Ask AgriGuard a question (RAG assistant)

```
POST http://localhost:5000/api/ai/ask
Content-Type: application/json

{
  "question": "How do I prevent Fall Armyworm?",
  "language": "en"
}
```

### Community outbreak risk

```
POST http://localhost:5000/api/ai/community-risk
Content-Type: application/json

{
  "reports": [ ...list of report objects... ]
}
```

### Full demo (all scenarios in one call)

```
GET http://localhost:5000/api/ai/demo
```

---

## Step 5 — What to display in the UI for each AI result field

```
confidence_score >= 0.80  →  🟢 High confidence badge
confidence_score >= 0.50  →  🟡 Medium confidence badge
confidence_score <  0.50  →  🔴 Low confidence — show escalation banner

detected_severity = "LOW"      →  green chip
detected_severity = "MODERATE" →  orange chip
detected_severity = "HIGH"     →  red chip
detected_severity = "CRITICAL" →  dark red chip + escalation banner

needs_agronomist = true  →  Show: "⚠️ Agronomist review recommended"

is_mock = true           →  Show: "🧪 Demo result" badge

disclaimer field          →  Always display at bottom of every AI result card
```

**IMPORTANT:** Always display the `disclaimer` field.
Never hide it. The AI is not a substitute for a qualified agronomist.

---

## Step 6 — Language support (EN / RW)

Both services support English (`en`) and Kinyarwanda (`rw`).

Pass `"language": "rw"` or `"language": "en"` in your request body.
The AI service auto-detects the language from the text if you pass `"language": "auto"`.

The backend stores `preferred_language` on each farmer profile —
read this when the farmer logs in and pass it to every AI request.

---

## Step 7 — Channels the UI does NOT need to build

| Channel | Built by | How it works |
|---------|----------|-------------|
| USSD | Person 3 (backend) | Africa's Talking gateway → `/api/v1/ussd` |
| IVR / Voice call | Person 3 (backend) | Voice gateway → `/api/v1/ivr` |
| AI Voice demo | Person 2 (Colab notebook) | Section 17 of the notebook |

The UI only needs to build the **smartphone app** (web or mobile).

---

## Step 8 — CORS (already configured)

Both services have CORS enabled for all origins in development:

```
AI Service (port 5000):  allow_origins=["*"]
Backend    (port 8000):  allow_origins=["*"]
```

No CORS configuration needed in the UI for local development.
For production, Person 3 will set `allow_origins` to the production domain.

---

## Step 9 — Environment variables for the UI

Create a `.env` file in your UI project:

```
# Local development
VITE_BACKEND_URL=http://localhost:8000/api/v1
VITE_AI_SERVICE_URL=http://localhost:5000/api/ai

# Production (update when deployed)
# VITE_BACKEND_URL=https://api.agriguard.rw/api/v1
# VITE_AI_SERVICE_URL=https://ai.agriguard.rw/api/ai
```

---

## Step 10 — Quick integration checklist for Person 1

- [ ] Start AI service on port 5000 (`uvicorn app.main:app --port 5000`)
- [ ] Start backend on port 8000 (`python backend/run.py`)
- [ ] Set `AI_SERVICE_URL=http://localhost:5000/api/v1/predict` in `backend/.env`
- [ ] Register a test farmer via `POST /api/v1/auth/register`
- [ ] Login and store the JWT token
- [ ] Submit a report via `POST /api/v1/reports/` with the token
- [ ] Upload a photo via `POST /api/v1/reports/{id}/images`
- [ ] Display the `ai_result` fields in the UI
- [ ] Show `confidence_score` as a badge (High/Medium/Low)
- [ ] Show `detected_severity` as a coloured chip
- [ ] Show escalation banner when `needs_agronomist = true`
- [ ] Always display the `disclaimer` field
- [ ] Pass `preferred_language` from farmer profile to AI requests
- [ ] Test with both `"language": "en"` and `"language": "rw"`

---

## Full API documentation

- Backend: `http://localhost:8000/docs` (Swagger UI — auto-generated)
- AI Service: `http://localhost:5000/docs` (Swagger UI — auto-generated)
