"""AgriGuard AI & Data component — Google Colab / ML experimentation layer.

This package is the Colab-runnable, ML-rich implementation of the AgriGuard AI
and data layer (Person 2). It is intentionally self-contained so it can be opened
in Google Colab, run, and demonstrated without the FastAPI server.

Layout:
    ai/src/        — Python AI/ML modules (classification, RAG, confidence,
                    severity, outbreak detection, 5 km alert, multilingual,
                    vision abstraction, crop-analysis orchestrator, data models)
    ai/data/       — prototype CSV datasets (crops, problems, knowledge, reports)
    ai/notebooks/  — the Google Colab demonstration notebook
    ai/tests/      — pytest tests

Relationship to the sibling ``app/`` package:
    ``app/`` is the deployable FastAPI service that Persons 1 (frontend) and 3
    (backend) call over HTTP. ``ai/`` is the Colab/ML layer that implements the
    same domain contracts with real ML (scikit-learn classification,
    sentence-transformers + FAISS RAG) on top of the same prototype data.
    The FastAPI service can later delegate to these ML modules; the notebook is
    the primary demonstration surface.
"""

__version__ = "1.0.0"
