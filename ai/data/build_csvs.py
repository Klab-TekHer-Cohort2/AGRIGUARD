"""Generate the prototype CSV datasets from the canonical knowledge base.

Single source of truth: the structured knowledge base lives in
``app/data/knowledge_base/`` and the prototype reports/farmers in
``app/data/prototype_dataset.py``. This script exports them to CSV so the
Google Colab notebook can ``pd.read_csv`` them directly.

Run from the repository root:

    python -m ai.data.build_csvs

The output is clearly PROTOTYPE data (see the ``is_prototype`` marker columns).
"""

import csv
import os

from app.data import knowledge_base as kb
from app.data.prototype_dataset import prototype_dataset as dataset


def _join(values):
    """Join a list into a single pipe-delimited CSV cell."""
    return " | ".join(str(v) for v in values if v is not None)


def _write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_crops(path):
    rows = []
    for c in kb.crops:
        rows.append(
            {
                "id": c["id"],
                "name_en": c["name"]["en"],
                "name_rw": c["name"]["rw"],
                "scientific_name": c["scientificName"],
                "description_en": c["description"]["en"],
                "description_rw": c["description"]["rw"],
                "growing_seasons": _join(c["growingSeasons"]),
                "altitude_range": c["altitudeRange"],
                "common_problems": _join(c["commonProblems"]),
                "prevention_tips_en": _join(c["preventionTips"]["en"]),
                "prevention_tips_rw": _join(c["preventionTips"]["rw"]),
                "expert_contact": c["expertContact"],
            }
        )
    _write_csv(
        path,
        [
            "id", "name_en", "name_rw", "scientific_name", "description_en",
            "description_rw", "growing_seasons", "altitude_range",
            "common_problems", "prevention_tips_en", "prevention_tips_rw",
            "expert_contact",
        ],
        rows,
    )
    return len(rows)


def build_crop_problems(path):
    rows = []
    for p in kb.problems:
        rows.append(
            {
                "id": p["id"],
                "name_en": p["name"]["en"],
                "name_rw": p["name"]["rw"],
                "scientific_name": p["scientificName"],
                "category": p["category"],
                "affected_crops": _join(p["affectedCrops"]),
                "severity_example": p["severityExample"],
                "symptoms_en": _join(p["symptoms"]["en"]),
                "symptoms_rw": _join(p["symptoms"]["rw"]),
                "recommendations_en": _join(p["recommendations"]["en"]),
                "recommendations_rw": _join(p["recommendations"]["rw"]),
                "confidence": p["confidence"],
                "keywords": _join(p["keywords"]),
            }
        )
    _write_csv(
        path,
        [
            "id", "name_en", "name_rw", "scientific_name", "category",
            "affected_crops", "severity_example", "symptoms_en", "symptoms_rw",
            "recommendations_en", "recommendations_rw", "confidence", "keywords",
        ],
        rows,
    )
    return len(rows)


def build_agricultural_knowledge(path):
    rows = []
    for a in kb.get_knowledge_articles():
        rows.append(
            {
                "id": a["id"],
                "title": a["title"],
                "crop": a["crop"],
                "topic": a["topic"],
                "content_en": a["contentEn"],
                "content_rw": a["contentRw"],
                "source": a["source"],
                "keywords": _join(a["keywords"]),
            }
        )
    _write_csv(
        path,
        ["id", "title", "crop", "topic", "content_en", "content_rw", "source", "keywords"],
        rows,
    )
    return len(rows)


def build_demo_reports(path):
    rows = []
    for r in dataset["reports"]:
        rows.append(
            {
                "report_id": r.get("id"),
                "farmer_id": r.get("farmerId"),
                "crop": r.get("crop"),
                "crop_id": r.get("cropId"),
                "problem": r.get("problem") or "",
                "problem_id": r.get("problemId") or "",
                "category": r.get("category"),
                "confidence": r.get("confidence"),
                "severity": r.get("severity"),
                "latitude": r.get("lat"),
                "longitude": r.get("lng"),
                "community": r.get("community"),
                "timestamp": r.get("timestamp"),
                "is_prototype": True,
            }
        )
    _write_csv(
        path,
        [
            "report_id", "farmer_id", "crop", "crop_id", "problem", "problem_id",
            "category", "confidence", "severity", "latitude", "longitude",
            "community", "timestamp", "is_prototype",
        ],
        rows,
    )
    return len(rows)


def build_demo_farmers(path):
    rows = []
    for f in dataset["farmers"]:
        rows.append(
            {
                "farmer_id": f.get("id"),
                "name": f.get("name"),
                "latitude": f.get("lat"),
                "longitude": f.get("lng"),
                "phone": f.get("phone") or "",
                "community": f.get("community"),
                "is_prototype": True,
            }
        )
    _write_csv(
        path,
        ["farmer_id", "name", "latitude", "longitude", "phone", "community", "is_prototype"],
        rows,
    )
    return len(rows)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    counts = {
        "crops.csv": build_crops(os.path.join(here, "crops.csv")),
        "crop_problems.csv": build_crop_problems(os.path.join(here, "crop_problems.csv")),
        "agricultural_knowledge.csv": build_agricultural_knowledge(os.path.join(here, "agricultural_knowledge.csv")),
        "demo_reports.csv": build_demo_reports(os.path.join(here, "demo_reports.csv")),
        "demo_farmers.csv": build_demo_farmers(os.path.join(here, "demo_farmers.csv")),
    }
    print("Generated prototype CSV datasets in", here)
    for name, n in counts.items():
        print(f"  {name:35s} {n:4d} rows")
    print("\nNOTE: all files are PROTOTYPE / demo data — not real outbreak records.")


if __name__ == "__main__":
    main()
