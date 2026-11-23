# FloraGuard Backend

FastAPI backend for pest/disease reporting, risk prediction, alerts, USSD/IVR intake, and map aggregation.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Environment

Copy `.env.example` to `.env`. Key variables:
- `DATABASE_URL` (default SQLite)
- `WEATHER_BASE_URL`, `WEATHER_TIMEOUT_SECONDS`
- `AI_MODEL_PATH` (optional, format `package.module:function`)
- `RISK_WINDOW_HOURS`, `RISK_SCORE_LOW_MAX`, `RISK_SCORE_MEDIUM_MAX`
- `SMS_PROVIDER` (leave empty; no SMS delivery claimed)

## Endpoints

- GET /api/health
- POST /api/reports
- GET /api/reports
- GET /api/reports/{id}
- GET /api/risk
- GET /api/alerts
- POST /api/ussd
- POST /api/ivr
- GET /api/map/reports

## AI model integration (Member 1)

Implement `predict_image(image_path: str) -> Optional[dict]` returning `problem_type`, `confidence`, optional `description`. Set `AI_MODEL_PATH=your.module:predict_image`. If unavailable, API continues without fake predictions.

## Tests

```bash
python -m pytest -v
```

## Limitations

- SMS delivery not configured; alert delivery_status is SKIPPED.
- Risk rules are prototype heuristics, not scientifically validated.
- No real telecom provider integration.
