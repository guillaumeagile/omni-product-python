"""Le barème des règles et la table de la scorecard, sur des cas dont on connaît le total."""

from harness.rules.points import (
    BABY_STEP_POINTS,
    EMPTY_PR_POINTS,
    METRIC_CAP,
    REGRESSED_POINTS,
    REMOVED_ON_RED_CAP,
    TURNED_GREEN_POINTS,
    RuleResult,
    metric_points,
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


def test_a_rule_going_back_to_red_costs_points():
    result = score((rule(1, 0, 3),))

    assert [r.number for r in result.regressed] == [1]
    assert result.regression_points == REGRESSED_POINTS
    assert result.total == REGRESSED_POINTS


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


def test_a_lower_is_better_metric_going_up_loses_points_and_going_down_gains_them():
    assert metric_points(4, -1) == -4
    assert metric_points(-4, -1) == 4


def test_a_higher_is_better_metric_going_up_gains_points():
    # TCC et lambdas : une hausse va dans le bon sens.
    assert metric_points(3, +1) == 3
    assert metric_points(-3, +1) == -3


def test_each_metric_is_capped_at_ten_in_both_directions():
    assert metric_points(-25, -1) == METRIC_CAP == 15
    assert metric_points(25, -1) == -15


def test_a_weight_of_zero_neutralises_the_metric():
    assert metric_points(-25, -1, weight=0) == 0
    assert metric_points(25, +1, weight=0) == 0


def test_a_weight_multiplies_the_points_before_the_cap():
    assert metric_points(4, -1, weight=2) == -8
    assert metric_points(4, -1, weight=3) == -12
    assert metric_points(4, -1, weight=5) == -15  # 20 points, plafonnés à -15
    assert metric_points(4, -1, weight=0.5) == -2


def test_a_fractional_variation_is_rounded_to_whole_points():
    assert metric_points(0.4, -1) == 0
    assert metric_points(2.6, -1) == -3


def test_metric_points_add_to_the_total_next_to_the_rules():
    # Une règle verte (+10), baby step (+5), métriques : -4 et +3 (-1 au total).
    result = score((rule(1, 2, 0),), metric_lines=(("Complexité", -4), ("Lambdas", 3)))

    assert result.metric_points == -1
    assert result.total == 10 + 5 - 1


def test_the_table_shows_the_points_of_each_metric():
    text = section(
        (rule(1, 2, 0),), metric_lines=(("Complexité", -4), ("Lambdas", metric_points(20, +1)))
    )

    assert "| Métrique : Complexité (plafond ±15) | -4 |" in text
    assert "| Métrique : Lambdas (plafond ±15) | +15 |" in text
    assert "| **Total** | **+26** |" in text


def test_a_negative_total_shows_a_single_sign():
    text = section((rule(1, 2, 0),), metric_lines=(("Complexité", -20),))

    assert "| **Total** | **-5** |" in text
    assert "+-" not in text


def test_an_empty_pr_loses_points():
    assert score((rule(1, 2, 2),), changed_tokens=0).total == EMPTY_PR_POINTS == -5
    assert score((rule(1, 2, 2),), changed_tokens=3).empty_pr_points == 0
    assert score((rule(1, 2, 2),)).empty_pr_points == 0  # tokens modifiés inconnus


def test_the_table_shows_the_empty_pr_line_only_when_the_pr_is_empty():
    empty = section((rule(1, 2, 2),), changed_tokens=0)
    changed = section((rule(1, 2, 2),), changed_tokens=3)

    assert "| 🫥 PR vide : aucun token de code modifié | -5 |" in empty
    assert "| **Total** | **-5** |" in empty
    assert "PR vide" not in changed
