"""Knowledge base loader for the Colab AI component.

Loads the prototype CSV datasets (``ai/data/*.csv``) into pandas DataFrames and
exposes convenient lookup helpers + parsed dict views (list fields are split
back into Python lists). This is the single data-access point for the rest of
``ai/src``: classification, RAG, recommendations, and crop-analysis all read
from here, so swapping the CSVs swaps the knowledge for the whole pipeline.

All data loaded here is PROTOTYPE / demo data (see the ``is_prototype`` columns
in the report/farmer CSVs). It is NOT real current outbreak data.
"""

import os
from functools import lru_cache
from typing import Dict, List, Optional

import pandas as pd

# Resolve the data directory relative to this file: ai/src -> ai/data
_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))


def data_dir() -> str:
    """Return the prototype data directory (overridable for tests)."""
    return os.environ.get("AGRIGUARD_DATA_DIR", _DATA_DIR)


def _path(name: str) -> str:
    return os.path.join(data_dir(), name)


def _split_pipe(value) -> List[str]:
    """Split a pipe-delimited CSV cell back into a list (empty -> [])."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    s = str(value).strip()
    if not s:
        return []
    return [part.strip() for part in s.split("|") if part.strip()]


@lru_cache(maxsize=1)
def crops_df() -> pd.DataFrame:
    return pd.read_csv(_path("crops.csv"))


@lru_cache(maxsize=1)
def problems_df() -> pd.DataFrame:
    return pd.read_csv(_path("crop_problems.csv"))


@lru_cache(maxsize=1)
def knowledge_df() -> pd.DataFrame:
    return pd.read_csv(_path("agricultural_knowledge.csv"))


@lru_cache(maxsize=1)
def reports_df() -> pd.DataFrame:
    return pd.read_csv(_path("demo_reports.csv"))


@lru_cache(maxsize=1)
def farmers_df() -> pd.DataFrame:
    return pd.read_csv(_path("demo_farmers.csv"))


def reload_data() -> None:
    """Clear the cached DataFrames (call after editing CSVs in a notebook)."""
    crops_df.cache_clear()
    problems_df.cache_clear()
    knowledge_df.cache_clear()
    reports_df.cache_clear()
    farmers_df.cache_clear()


# ── Parsed dict views (list fields restored) ──────────────────────────────────
def problems_as_dicts() -> List[Dict]:
    """Return problems as a list of dicts with list fields parsed.

    Keys: id, name_en, name_rw, scientific_name, category, affected_crops (list),
    severity_example, symptoms_en/rw (list), recommendations_en/rw (list),
    confidence (float), keywords (list).
    """
    out = []
    for _, r in problems_df().iterrows():
        out.append(
            {
                "id": r["id"],
                "name_en": r["name_en"],
                "name_rw": r["name_rw"],
                "scientific_name": r["scientific_name"],
                "category": r["category"],
                "affected_crops": _split_pipe(r["affected_crops"]),
                "severity_example": r["severity_example"],
                "symptoms_en": _split_pipe(r["symptoms_en"]),
                "symptoms_rw": _split_pipe(r["symptoms_rw"]),
                "recommendations_en": _split_pipe(r["recommendations_en"]),
                "recommendations_rw": _split_pipe(r["recommendations_rw"]),
                "confidence": float(r["confidence"]),
                "keywords": _split_pipe(r["keywords"]),
            }
        )
    return out


def crops_as_dicts() -> List[Dict]:
    """Return crops as a list of dicts with list fields parsed."""
    out = []
    for _, r in crops_df().iterrows():
        out.append(
            {
                "id": r["id"],
                "name_en": r["name_en"],
                "name_rw": r["name_rw"],
                "scientific_name": r["scientific_name"],
                "description_en": r["description_en"],
                "description_rw": r["description_rw"],
                "growing_seasons": _split_pipe(r["growing_seasons"]),
                "altitude_range": r["altitude_range"],
                "common_problems": _split_pipe(r["common_problems"]),
                "prevention_tips_en": _split_pipe(r["prevention_tips_en"]),
                "prevention_tips_rw": _split_pipe(r["prevention_tips_rw"]),
                "expert_contact": r["expert_contact"],
            }
        )
    return out


# ── Lookups ───────────────────────────────────────────────────────────────────
def get_problem_by_id(problem_id: str) -> Optional[Dict]:
    for p in problems_as_dicts():
        if p["id"] == problem_id:
            return p
    return None


def get_crop_by_id(crop_id: str) -> Optional[Dict]:
    for c in crops_as_dicts():
        if c["id"] == crop_id:
            return c
    return None


def get_crop_by_name(name: str) -> Optional[Dict]:
    """Find a crop by id, English/Rw name, or scientific name (case-insensitive)."""
    lower = (name or "").lower().strip()
    if not lower:
        return None
    for c in crops_as_dicts():
        if (
            c["id"] == lower
            or c["name_en"].lower() == lower
            or c["name_rw"].lower() == lower
            or c["scientific_name"].lower() == lower
        ):
            return c
    return None


def get_problems_by_crop(crop_id: str) -> List[Dict]:
    return [p for p in problems_as_dicts() if crop_id in p["affected_crops"]]


def knowledge_articles_as_dicts() -> List[Dict]:
    """Return the flattened knowledge articles (for RAG) with keywords parsed."""
    out = []
    for _, r in knowledge_df().iterrows():
        out.append(
            {
                "id": r["id"],
                "title": r["title"],
                "crop": r["crop"],
                "topic": r["topic"],
                "content_en": r["content_en"],
                "content_rw": r["content_rw"],
                "source": r["source"],
                "keywords": _split_pipe(r["keywords"]),
            }
        )
    return out


def reports_as_dicts() -> List[Dict]:
    """Return demo reports with snake_case keys matching OutbreakRisk input."""
    out = []
    for _, r in reports_df().iterrows():
        out.append(
            {
                "report_id": r["report_id"],
                "farmer_id": r["farmer_id"],
                "crop": r["crop"],
                "crop_id": r["crop_id"],
                "problem": r["problem"] if pd.notna(r["problem"]) else None,
                "problem_id": r["problem_id"] if pd.notna(r["problem_id"]) else None,
                "category": r["category"],
                "confidence": float(r["confidence"]),
                "severity": r["severity"],
                "latitude": float(r["latitude"]) if pd.notna(r["latitude"]) else None,
                "longitude": float(r["longitude"]) if pd.notna(r["longitude"]) else None,
                "community": r["community"],
                "timestamp": r["timestamp"],
            }
        )
    return out


def farmers_as_dicts() -> List[Dict]:
    """Return demo farmers in the shape expected by farmers_within_radius()."""
    out = []
    for _, r in farmers_df().iterrows():
        out.append(
            {
                "id": r["farmer_id"],
                "name": r["name"],
                "lat": float(r["latitude"]) if pd.notna(r["latitude"]) else None,
                "lng": float(r["longitude"]) if pd.notna(r["longitude"]) else None,
                "phone": r["phone"] if pd.notna(r["phone"]) else None,
                "community": r["community"],
            }
        )
    return out
