from __future__ import annotations

from smvc_api.models import ClassificationResult

# Default threshold aligned with [M3] fail-safe (skip when uncertain).
DEFAULT_SCENERY_THRESHOLD = 0.72


def classify_scenery_placeholder(
    *,
    clip_features: dict[str, float],
    threshold: float = DEFAULT_SCENERY_THRESHOLD,
) -> ClassificationResult:
    """
    Stand-in for a real video classifier. [M2] score + label + explanation.

    `clip_features` keys are test fixtures (e.g. nature_score, people_score).
    """
    nature = clip_features.get("nature_score", 0.0)
    people = clip_features.get("people_score", 0.0)
    score = max(0.0, min(1.0, nature * (1.0 - people)))
    is_scenery = score >= threshold
    label = "scenery_only" if is_scenery else "not_scenery_only"
    explanation = f"nature={nature:.2f}, people={people:.2f}, threshold={threshold:.2f}"
    return ClassificationResult(
        score=score,
        label=label,
        is_scenery_only=is_scenery,
        explanation=explanation,
    )
