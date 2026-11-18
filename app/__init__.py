"""AgriGuard AI & Data Layer — Python package.

This package contains the full AI/data layer of AgriGuard, reimplemented in
Python with FastAPI. It exposes the same HTTP API and JSON contracts as the
previous Node.js/Express implementation, so the backend and UI teammates are
unaffected by the language change.

Subpackages:
    config                 — runtime settings (env-driven)
    data.knowledge_base    — prototype crop/problem knowledge base + RAG articles
    data.prototype_dataset  — demo farmers, reports, scenarios
    services               — crop analysis, RAG, assistant, outbreak, escalation, language, USSD
    services.adapters      — vision/text adapters (mock + OpenAI)
    utils                  — geo helpers (Haversine, radius queries)
    routes                 — FastAPI APIRouter for /api/ai/*
    middleware             — error handling
"""

__version__ = "1.0.0"
