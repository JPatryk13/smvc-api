"""Classifier tests. Docstrings quote criteria from tests/acceptance/REQUIREMENTS.md."""

import pytest

from smvc_api.classifier import DEFAULT_SCENERY_THRESHOLD, classify_scenery_placeholder


@pytest.mark.parametrize(
    ("features", "threshold", "expect_scenery"),
    [
        ({"nature_score": 0.95, "people_score": 0.0}, DEFAULT_SCENERY_THRESHOLD, True),
        ({"nature_score": 0.3, "people_score": 0.8}, DEFAULT_SCENERY_THRESHOLD, False),
        ({"nature_score": 0.8, "people_score": 0.1}, 0.99, False),
    ],
)
def test_scenery_selection_threshold(
    features: dict[str, float],
    threshold: float,
    expect_scenery: bool,
) -> None:
    """**M2** — Each decision exposes at least **score**, **label**, and optionally **explanation**; **threshold** is configurable.

    **M3** — Below threshold → **skip** upload; when in doubt, favor **false negatives** if privacy-sensitive.
    """

    # Given fixture feature weights and a score threshold (parametrized).
    # When the placeholder classifier scores the clip.
    result = classify_scenery_placeholder(clip_features=features, threshold=threshold)

    # Then is_scenery_only matches expect_scenery; score is bounded and explanation is present.
    assert result.is_scenery_only is expect_scenery
    assert 0.0 <= result.score <= 1.0
    assert result.explanation


def test_m2_outputs_score_label_explanation() -> None:
    """**M2** — Each decision exposes at least **score**, **label**, and optionally **explanation**; **threshold** is configurable."""

    # Given a strongly "nature / no people" feature vector.
    # When classifying with default threshold.
    r = classify_scenery_placeholder(
        clip_features={"nature_score": 1.0, "people_score": 0.0}
    )

    # Then label is one of the expected strings and score is ~1.0.
    assert r.label in ("scenery_only", "not_scenery_only")
    assert r.score == pytest.approx(1.0)
