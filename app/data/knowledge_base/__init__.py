"""Knowledge Base index — central access point for prototype agricultural knowledge.

This module mirrors ``src/data/knowledgeBase/index.js``. It exposes the crop and
problem lists plus lookup/search helpers and the flattened knowledge articles
used by the RAG service.

Import as::

    from app.data import knowledge_base as kb
    kb.get_crop_by_id("maize")
"""

from app.data.knowledge_base.crops import crops
from app.data.knowledge_base.problems import problems

__all__ = [
    "crops",
    "problems",
    "get_crop_by_id",
    "get_crop_by_name",
    "get_problem_by_id",
    "get_problem_by_name",
    "get_problems_by_crop",
    "get_problems_by_category",
    "get_categories",
    "search_problems",
    "get_knowledge_articles",
]


def get_crop_by_id(crop_id):
    """Return the crop dict with the given id, or None."""
    return next((c for c in crops if c["id"] == crop_id), None)


def get_crop_by_name(name):
    """Find a crop by id, English/Kinyarwanda name, or scientific name (case-insensitive)."""
    lower = (name or "").lower().strip()
    if not lower:
        return None
    return next(
        (
            c
            for c in crops
            if c["id"] == lower
            or c["name"]["en"].lower() == lower
            or c["name"]["rw"].lower() == lower
            or c["scientificName"].lower() == lower
        ),
        None,
    )


def get_problem_by_id(problem_id):
    """Return the problem dict with the given id, or None."""
    return next((p for p in problems if p["id"] == problem_id), None)


def get_problem_by_name(name):
    """Find a problem by id or English/Kinyarwanda name (case-insensitive)."""
    lower = (name or "").lower().strip()
    if not lower:
        return None
    return next(
        (
            p
            for p in problems
            if p["id"] == lower
            or p["name"]["en"].lower() == lower
            or p["name"]["rw"].lower() == lower
        ),
        None,
    )


def get_problems_by_crop(crop_id):
    """Return all problems that affect the given crop id."""
    return [p for p in problems if crop_id in p["affectedCrops"]]


def get_problems_by_category(category):
    """Return all problems in a given category."""
    return [p for p in problems if p["category"] == category]


def get_categories():
    """Return the distinct set of problem categories, in knowledge-base order."""
    seen = []
    for p in problems:
        if p["category"] not in seen:
            seen.append(p["category"])
    return seen


def search_problems(query):
    """Search problems by keyword overlap with the query (case-insensitive)."""
    q = (query or "").lower().strip()
    if not q:
        return []
    return [p for p in problems if any(kw.lower() in q for kw in p["keywords"])]


def get_knowledge_articles():
    """Flatten the knowledge base into a list of searchable text chunks for RAG.

    Each article has: id, title, crop, topic, contentEn, contentRw, source, keywords.
    """
    articles = []

    for crop in crops:
        articles.append(
            {
                "id": f"crop-{crop['id']}",
                "title": f"{crop['name']['en']} ({crop['scientificName']})",
                "crop": crop["id"],
                "topic": "crop-overview",
                "contentEn": (
                    f"{crop['description']['en']} Grown in {crop['altitudeRange']}. "
                    f"Seasons: {', '.join(crop['growingSeasons'])}. "
                    f"Common problems include: {', '.join(crop['commonProblems'])}."
                ),
                "contentRw": (
                    f"{crop['description']['rw']} Biragundwa mu {crop['altitudeRange']}. "
                    f"Ibihe: {', '.join(crop['growingSeasons'])}."
                ),
                "source": "AgriGuard Prototype Knowledge Base",
                "keywords": [
                    crop["id"],
                    crop["name"]["en"].lower(),
                    crop["name"]["rw"].lower(),
                    crop["scientificName"].lower(),
                ],
            }
        )

        articles.append(
            {
                "id": f"crop-{crop['id']}-prevention",
                "title": f"{crop['name']['en']} prevention tips",
                "crop": crop["id"],
                "topic": "prevention",
                "contentEn": (
                    f"Prevention tips for {crop['name']['en']}: "
                    f"{' '.join(crop['preventionTips']['en'])}"
                ),
                "contentRw": (
                    f"Inama zo kurinda {crop['name']['rw']}: "
                    f"{' '.join(crop['preventionTips']['rw'])}"
                ),
                "source": "AgriGuard Prototype Knowledge Base",
                "keywords": [crop["id"], "prevention", "tips"],
            }
        )

    for problem in problems:
        articles.append(
            {
                "id": f"problem-{problem['id']}",
                "title": f"{problem['name']['en']} ({problem['category']})",
                "crop": ",".join(problem["affectedCrops"]),
                "topic": problem["category"].lower(),
                "contentEn": (
                    f"{problem['name']['en']} affects {', '.join(problem['affectedCrops'])}. "
                    f"Symptoms: {' '.join(problem['symptoms']['en'])}. "
                    f"Recommendations: {' '.join(problem['recommendations']['en'])}"
                ),
                "contentRw": (
                    f"{problem['name']['rw']} ingenzi ku {', '.join(problem['affectedCrops'])}. "
                    f"Ibimenyetso: {' '.join(problem['symptoms']['rw'])}. "
                    f"Inama: {' '.join(problem['recommendations']['rw'])}"
                ),
                "source": "AgriGuard Prototype Knowledge Base",
                "keywords": problem["keywords"],
            }
        )

    return articles
