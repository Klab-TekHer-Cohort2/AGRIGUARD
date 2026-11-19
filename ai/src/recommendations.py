"""Recommendation generation (section 5).

Produces a localised, actionable recommendation list for an identified problem.
Falls back to crop-specific general advice when the problem is unknown, and to a
generic extension-officer message when even the crop is unknown.
"""

from typing import List, Optional

from ai.src import knowledge
from ai.src.multilingual import get_message, localise_list
from ai.src.severity import ESCALATE_SEVERITIES


def generate_recommendation(
    crop_id: Optional[str],
    problem: Optional[dict],
    lang: str = "en",
    severity: Optional[str] = None,
) -> List[str]:
    """Generate a localised recommendation list.

    - Known problem  -> that problem's recommendations (+ escalation note if
      severity is High/Critical, even when the problem is confidently known).
    - Unknown problem, known crop -> the crop's first 3 prevention tips.
    - Unknown crop -> a generic extension-officer message.
    """
    crop = knowledge.get_crop_by_id(crop_id) if crop_id else None

    if problem:
        recs_key = "recommendations_en" if lang != "rw" else "recommendations_rw"
        recs = list(problem.get(recs_key) or problem.get("recommendations_en") or [])
        if severity in ESCALATE_SEVERITIES:
            recs = list(recs)
            recs.append(
                get_message("needs_agronomist", lang)
                + " — " + get_message("disclaimer", lang)
            )
        return recs

    if crop:
        tips_key = "prevention_tips_en" if lang != "rw" else "prevention_tips_rw"
        return list((crop.get(tips_key) or crop.get("prevention_tips_en"))[:3])

    return [
        "Genzura umurima wawe kandi usabe inama z'umuhinzi w'ubuhinza."
        if lang == "rw"
        else "Inspect your field and seek advice from an agricultural extension officer."
    ]
