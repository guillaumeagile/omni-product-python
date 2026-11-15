"""Le barème des règles et la table de la scorecard, sur des cas dont on connaît le total."""

from harness.rules.points import (
    BABY_STEP_POINTS,
    REMOVED_ON_RED_CAP,
    TURNED_GREEN_POINTS,
    RuleResult,
    score,
)
from harness.rules.report import section


def rule(number: int, before: int | None, after: int) -> RuleResult:
    return RuleResult(number=number, title=f"Règle {number}", before=before, after=after)


def test_one_rule_turned_green_with_a_reduction_elsewhere_is_a_baby_step():
    result = score((rule(1, 2, 0), rule(2, 4, 2)))

    assert result.green_points == TURNED_GREEN_POINTS
    assert result.removed_points == 2  # 4 → 2 sur la règle encore rouge
    assert result.baby_step_points == BABY_STEP_POINTS
    assert result.total == 10 + 2 + 5


def test_two_rules_turned_green_is_not_a_baby_step():
    result = score((rule(1, 2, 0), rule(2, 3, 0)))

    assert result.green_points == 2 * TURNED_GREEN_POINTS
    assert result.baby_step_points == 0
    assert result.total == 20


def test_removals_on_red_rules_are_capped():
    result = score((rule(1, 30, 5),))

    assert result.removed_points == REMOVED_ON_RED_CAP
    assert result.total == REMOVED_ON_RED_CAP


def test_without_base_nothing_is_scored():
    result = score((rule(1, None, 4),))

    assert result.total == 0
    assert result.turned_green == ()


def test_a_rule_missing_from_the_base_is_not_scored():
    # Une règle qui n'existait pas dans la base ne peut pas être « passée au vert » par la PR.
    result = score((rule(1, None, 0),))

    assert result.total == 0


def test_a_rule_going_back_to_red_is_a_regression_without_points_lost():
    result = score((rule(1, 0, 3),))

    assert [r.number for r in result.regressed] == [1]
    assert result.total == 0


def test_the_table_shows_each_rule_and_the_score():
    text = section((rule(1, 2, 0), rule(2, 4, 2)))

    assert "| 1 · Règle 1 | 🔴 FAIL (2) | 🟢 PASS | +10 |" in text
    assert "| 2 · Règle 2 | 🔴 FAIL (4) | 🔴 FAIL (2) |  |" in text
    assert "| **Total** | **+17** |" in text


def test_without_base_the_table_has_no_score():
    text = section((rule(1, None, 4),))

    assert "| 1 · Règle 1 | — | 🔴 FAIL (4) |  |" in text
    assert "Pas de base comparable" in text
    assert "| **Total**" not in text
