# AgriGuard AI & Data Layer — Documentation

> This layer is implemented in **Python** with **FastAPI**. All endpoints and
> JSON contracts are identical to the previous Node.js/Express version, so the
> backend and UI teammates are unaffected by the language change.

## 1. AI Architecture

The AI/data layer is a standalone Python/FastAPI service. All AI logic lives in
service modules under `app/services/`. No AI logic is placed in route handlers
or UI components.

```
Farmer Input (Smartphone / USSD / IVR)
        ↓
┌─────────────────────────────────────────────┐
│            cropAnalysisService                │
│  analyseCropReport(crop, description, image, │
│                    location, language)         │
│        ↓                                     │
│  imageAnalysisService (mock or OpenAI vision)│
│        ↓                                     │
│  classifyCropProblem → category + problem    │
│  calculateConfidence  → tier (high/med/low) │
│  calculateSeverity    → Low/Moderate/High/Crit│
│  generateRecommendation → localised advice   │
│  escalationService    → needsAgronomist?     │
│        ↓                                     │
│  CropAnalysisResult (structured JSON)        │
└─────────────────────────────────────────────┘
        ↓                           ↓
   Save Report              Ask AgriGuard
        ↓                           ↓
┌──────────────────┐   ┌─────────────────────────┐
│ outbreakDetection │   │  aiAssistantService     │
│ Service           │   │  question → detect lang │
│                   │   │  → ragService.retrieve   │
│ Group reports by  │   │  → grounded answer       │
│ problem+crop+geo  │   │  → escalation if needed  │
│ + recency         │   └─────────────────────────┘
│                   │
│ Score: count +    │
│ severity + conf + │
│ geo + recency     │
│        ↓          │
│ CommunityRiskResult│
│ (LOW/MED/HIGH/CRIT)│
│        ↓          │
│ findAlertableFarmers│
│ (5 km Haversine)  │
└──────────────────┘
        ↓
Alert / Agronomist
```

### Channels share one AI layer

Smartphone, USSD, and IVR all call the same `crop_analysis_service.analyse_crop_report()`. Only the formatting differs:

| Channel | Input | Output formatter |
|---------|-------|-----------------|
| Smartphone | crop + description + image + location | JSON `CropAnalysisResult` |
| USSD | crop + problemDescription + location | `ussdResponseFormatter` → short plain text |
| IVR | speech-to-text → same as USSD | same formatter (Kinyarwanda) |

There is no separate AI for USSD or IVR.

### Mock vs Real AI mode

Controlled by `AI_MODE` env var:

| Mode | Vision | Text/RAG | API key? |
|------|--------|----------|----------|
| `mock` (default) | `deterministic_mock_adapter` | local generator | No |
| `openai` | `openai_vision_adapter` (GPT-4o) | `openai_text_adapter` (GPT-4o-mini) | Yes |

Swapping mock→real only requires setting `AI_MODE=openai` and `OPENAI_API_KEY`. No code changes needed — the adapter interface is identical.

If `AI_MODE=openai` but the key is missing, the service gracefully falls back to mock and logs a warning.

> Adapters are pluggable. To add a Python-native ML model (e.g. a PyTorch/TensorFlow
> CNN trained on PlantVillage images, or a Hugging Face vision transformer), create
> a new adapter under `app/services/adapters/` exposing the same `analyse_image()`
> coroutine and add a branch in `image_analysis_service.select_adapter()`.

## 2. Output Contracts

### CropAnalysisResult

```json
{
  "category": "Pest",                    // Pest|Disease|NutrientDeficiency|EnvironmentalStress|Unknown
  "possibleProblem": "Fall Armyworm",    // localised problem name, or null if Unknown
  "problemId": "fall-armyworm",          // KB id, or null
  "confidence": 0.92,                     // 0.0–1.0
  "confidenceTier": "high",              // high|medium|low
  "confidenceLabel": "High",
  "severity": "Moderate",                // Low|Moderate|High|Critical
  "recommendation": ["Inspect...", "Monitor..."],  // localised list
  "recommendationText": "Inspect... Monitor...",
  "needsAgronomist": false,              // escalation decision
  "escalationReason": "none",            // comma-separated reasons
  "language": "en",                      // detected/used language
  "crop": "Maize",                       // localised crop name
  "cropId": "maize",
  "location": { "lat": -1.479, "lng": 30.419, "community": "Kabarore" },
  "imageAnalysed": true,
  "disclaimer": "Prototype AI assessment — not a substitute for professional agronomist advice.",
  "timestamp": "2026-11-17T..."
}
```

### CommunityRiskResult

```json
{
  "riskLevel": "CRITICAL",               // LOW|MEDIUM|HIGH|CRITICAL
  "riskScore": 84,                       // 0–100 heuristic (NOT a probability)
  "problem": "Fall Armyworm",
  "crop": "Maize",
  "cropId": "maize",
  "problemId": "fall-armyworm",
  "category": "Pest",
  "reportCount": 12,
  "affectedArea": "Kabarore",
  "affectedAreaCenter": { "lat": -1.480, "lng": 30.420 },
  "geoConcentrated": true,
  "alertRecommended": true,
  "reason": "cluster_detected",
  "radiusKm": 5,
  "timeWindowDays": 7,
  "prototype": true,
  "disclaimer": "Prototype risk detector — not a validated forecasting model."
}
```

### AgriculturalAnswer

```json
{
  "answer": "Based on our agricultural knowledge base: ...",
  "language": "en",
  "sources": [{ "title": "Fall Armyworm (Pest)", "source": "AgriGuard Prototype Knowledge Base", "topic": "pest" }],
  "confidence": 0.74,
  "needsAgronomist": false,
  "reason": "none"
}
```

## 3. API Contracts

All endpoints are under `/api/ai`.

### POST /api/ai/analyse-report

Analyse a single crop report (smartphone flow).

**Request:**
```json
{
  "crop": "Maize",                              // required
  "description": "Leaves have holes, small insects near whorl.",  // optional
  "image": "maize-armyworm.jpg",               // optional: filename, URL, base64, or Buffer
  "location": { "lat": -1.479, "lng": 30.419, "community": "Kabarore" },  // optional
  "language": "en",                             // optional: auto-detected if omitted
  "farmerRequestedHelp": false                  // optional: forces escalation if true
}
```

**Response (200):**
```json
{ "success": true, "data": { ...CropAnalysisResult } }
```

**Error (400):** missing `crop` field.
```json
{ "success": false, "error": "VALIDATION_ERROR", "message": "Field \"crop\" is required." }
```

### POST /api/ai/ask

Ask AgriGuard a free-form agricultural question.

**Request:**
```json
{
  "question": "How can I prevent Fall Armyworm in my maize?",  // required
  "language": "en",                  // optional: auto-detected if omitted
  "cropId": "maize"                   // optional: filters retrieval to this crop
}
```

**Response (200):**
```json
{ "success": true, "data": { ...AgriculturalAnswer } }
```

### POST /api/ai/community-risk

Analyse a set of farmer reports for community outbreak risk.

**Request:**
```json
{
  "reports": [ { ...farmerReport }, ... ],  // required: array of reports
  "timeWindowDays": 7,                      // optional: override default
  "alertRadiusKm": 5                         // optional: override default
}
```

Each farmer report should have: `farmerId, crop, cropId, problem, problemId, category, confidence, severity, lat, lng, community, timestamp`.

**Response (200):**
```json
{ "success": true, "data": { ...CommunityRiskResult } }
```

### POST /api/ai/outbreak-detection

Full outbreak detection including alertable farmers within the radius.

**Request:**
```json
{
  "reports": [ ... ],                    // required
  "farmers": [ { "id": "F001", "name": "...", "lat": -1.479, "lng": 30.419, "phone": "+250...", "community": "Kabarore" }, ... ],  // optional
  "timeWindowDays": 7,                   // optional
  "alertRadiusKm": 5                      // optional
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    ...CommunityRiskResult,
    "alertableFarmers": [ { "id": "F001", "name": "...", "community": "Kabarore", "distanceKm": 0.5, "phone": "+250..." } ],
    "alertableCount": 5
  }
}
```

### POST /api/ai/ussd-response

USSD channel: same AI layer, short plain-text output.

**Request:**
```json
{
  "farmerId": "F003",               // optional
  "crop": "Maize",                   // required
  "problemDescription": "Small insects eating maize leaves",  // optional
  "location": "Kabarore",           // optional
  "language": "en"                   // optional
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "farmerId": "F003",
    "ussdResponse": "Possible problem: Fall Armyworm\nConfidence: 92%\nSeverity: Moderate\nAdvice: Inspect nearby maize plants...\nStatus: Agronomist review not required",
    "analysis": { ...CropAnalysisResult }
  }
}
```

### GET /api/ai/demo

Runs the full hackathon demo scenario end-to-end. No request body needed.

Returns: `step1_smartphoneAnalysis`, `step2_unknownReport`, `step3_farmerRequestsHelp`, `step4_communityRisk`, `step4b_alertableFarmers`, `step5_askAgriGuardEnglish`, `step5b_askAgriGuardKinyarwanda`, `step6_ussdResponse`.

### GET /health

Returns service status and mode.

## 4. Data Sources

### Public/real sources (referenced for knowledge base content)

- **FAO** (Food and Agriculture Organization) — crop pest and disease descriptions
- **Rwanda Agriculture and Animal Resources Development Board (RAB)** — local agricultural guidance
- **CABI Crop Protection Compendium** — public summaries of pest/disease information

### Prototype/simulated data (NOT real)

- All farmer records in `app/data/prototype_dataset.py` are simulated. They do NOT represent real farmers or real outbreaks.
- All location coordinates are approximate community centroids, NOT individual farmer locations.
- The knowledge base in `app/data/knowledge_base/` is a curated subset for the prototype. It is not a complete agricultural reference.
- The mock image analysis returns deterministic results based on filename patterns — it does not perform real computer vision.

Every prototype dataset record and every outbreak result is marked with `prototype: true` and a disclaimer.

## 5. AI Limitations

| Limitation | Detail |
|-----------|--------|
| **Image quality** | Real vision models require clear, well-lit photos. Blurry, distant, or poor lighting images reduce accuracy significantly. The mock adapter does not perform real image analysis. |
| **Limited training data** | The knowledge base covers 5 crops and ~20 problems. Rwanda has hundreds of crop varieties and pests. The prototype cannot cover all. |
| **Kinyarwanda language** | Language detection uses a keyword heuristic, not a language model. Kinyarwanda responses are pre-written in the knowledge base, not generated. Complex or mixed-language questions may be misdetected. Do not assume perfect Kinyarwanda understanding. |
| **False positives** | The classifier may match a wrong problem when symptoms overlap (e.g., yellowing can indicate nitrogen deficiency OR disease). Medium/low confidence results ask for more information. |
| **False negatives** | A problem not in the knowledge base returns "Unknown." This does not mean the problem is not real — it means the AI cannot identify it. |
| **Need for agronomist verification** | The AI does NOT replace agronomists. High/critical severity always escalates. The AI provides initial guidance only. |
| **Prototype outbreak detection** | The risk score is a transparent heuristic (report count + severity + confidence + geo-concentration + recency), NOT a scientifically validated epidemiological model. It does not account for weather, crop stage, or pest life cycle. |
| **5 km radius** | Uses Haversine distance (straight-line). Real roads and terrain may make 5 km impractical. The radius is configurable via `ALERT_RADIUS_KM`. |
| **Privacy** | Only farmers with location data receive personalised radius alerts. The API does not expose exact private locations unnecessarily. |

## 6. Confidence and Severity Logic

### Confidence thresholds (configurable via env)

| Tier | Range | AI behaviour |
|------|-------|-------------|
| High | >= 0.80 | AI can provide an initial recommendation |
| Medium | 0.50–0.79 | AI asks for more information or another image |
| Low | < 0.50 | AI does not pretend to know; recommends agronomist review |

### Severity levels

`Low → Moderate → High → Critical`

Severity is **independent** of confidence. High confidence + High severity = the AI is confident the problem is serious. High/Critical severity always triggers agronomist escalation, even at high confidence.

### Agronomist escalation rules

Escalate (`needsAgronomist = true`) when ANY of:
- confidence < 0.50 (low confidence)
- severity == High
- severity == Critical
- category == Unknown
- farmer explicitly requested help
