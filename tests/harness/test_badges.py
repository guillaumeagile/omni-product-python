"""Les badges, sur des PR dont on change une seule mesure à la fois."""

import json
import textwrap
from dataclasses import replace
from pathlib import Path

from harness import badges, mutation, scorecard
from harness.metrics.report import measure
from harness.metrics.sources import SourceFile
from harness.rules.points import RuleResult
from harness.rules.report import section

BASE = measure(
    [
        SourceFile.from_text(
            "omni_product.domain.product",
            textwrap.dedent(
                """
                class Product:
                    def __init__(self):
                        self.name = ""
                """
            ),
        )
    ]
)
# Une PR neutre : aucune mesure ne bouge, un diff de taille moyenne.
NEUTRAL = badges.Pr(BASE, BASE, changed_tokens=1000)


def labels(pr: badges.Pr) -> list[str]:
    return [badge.label for badge in badges.earned(pr)]


def test_a_neutral_pr_earns_no_badge():
    assert labels(NEUTRAL) == []


def test_an_empty_pr_earns_no_badge():
    assert labels(replace(NEUTRAL, changed_tokens=0, head=replace(BASE, tokens=0))) == []


def test_a_small_diff_earns_its_badge_up_to_the_threshold():
    assert "🤏 Small diff" in labels(replace(NEUTRAL, changed_tokens=badges.SMALL_DIFF_TOKENS))
    assert "🤏 Small diff" not in labels(
        replace(NEUTRAL, changed_tokens=badges.SMALL_DIFF_TOKENS + 1)
    )


def test_clean_coder_needs_five_metric_points():
    assert "🧹 Clean Coder" in labels(replace(NEUTRAL, metric_lines=(("a", 3), ("b", 2))))
    assert "🧹 Clean Coder" not in labels(replace(NEUTRAL, metric_lines=(("a", 4),)))


def test_losing_tokens_is_less_is_more():
    assert "✂️ Less is more" in labels(replace(NEUTRAL, head=replace(BASE, tokens=BASE.tokens - 1)))


def test_uncle_bob_approves_a_drop_of_a_tenth_without_new_violation():
    base = replace(BASE, uncle_bob=0.44)

    assert "🧭 Uncle Bob approuve" in labels(
        replace(NEUTRAL, base=base, head=replace(BASE, uncle_bob=0.34))
    )
    assert "🧭 Uncle Bob approuve" not in labels(
        replace(NEUTRAL, base=base, head=replace(BASE, uncle_bob=0.35))
    )
    assert "🧭 Uncle Bob approuve" not in labels(
        replace(NEUTRAL, base=base, head=replace(BASE, uncle_bob=0.2, stability_violations=1))
    )


def test_fewer_mutable_attributes_is_immutable():
    base = replace(BASE, mutable_attributes=1)

    assert "🧊 Immuable" in labels(
        replace(NEUTRAL, base=base, head=replace(BASE, mutable_attributes=0))
    )


def test_badges_add_their_points_to_the_total():
    pr = replace(NEUTRAL, changed_tokens=10)
    text = section(
        (RuleResult(number=1, title="r", before=2, after=2),),
        changed_tokens=10,
        badge_lines=badges.lines(pr),
    )

    assert "| Badge 🤏 Small diff | +2 |" in text
    assert "| **Total** | **+2** |" in text


def test_no_base_no_badge():
    assert badges.lines(None) == ()


def test_a_higher_mutation_score_kills_mutants():
    assert "🧬 Tueur de mutants" in labels(replace(NEUTRAL, base_mutation=61.5, head_mutation=70.0))
    assert "🧬 Tueur de mutants" not in labels(
        replace(NEUTRAL, base_mutation=70.0, head_mutation=70.0)
    )
    assert "🧬 Tueur de mutants" not in labels(replace(NEUTRAL, head_mutation=90.0))


def test_the_mutation_score_is_read_from_the_ci_stats(tmp_path: Path):
    stats = tmp_path / "mutmut-cicd-stats.json"
    stats.write_text(json.dumps({"killed": 8, "total": 13, "survived": 5}))

    assert mutation.score(stats) == 61.5
    assert mutation.score(tmp_path / "absent.json") is None
    assert mutation.score(None) is None


def test_the_scorecard_shows_the_mutation_score_from_base_to_pr():
    card = scorecard.render(BASE, BASE, mutation=(61.5, 70.0))

    assert "| Score de mutation (modèle, % de mutants tués) | 61.5 | 70 | +8.5 | ✅ |" in card
    assert "Score de mutation" not in scorecard.render(BASE, BASE)


def test_the_badges_won_head_the_comment():
    pr = replace(
        NEUTRAL,
        changed_tokens=10,
        results=(RuleResult(number=1, title="r", before=2, after=0),),
    )
    card = scorecard.render(BASE, BASE, badges_md=badges.banner(badges.won(pr)))

    assert "![🍼 Baby step +5](https://img.shields.io/badge/" in card
    assert "![🤏 Small diff +2](https://img.shields.io/badge/" in card
    assert card.index("🏅 Badges gagnés") < card.index("📏 Métriques")


def test_no_badge_no_banner():
    assert badges.banner(badges.won(NEUTRAL)) == ""
    assert badges.won(None) == ()
    assert badges.won(replace(NEUTRAL, changed_tokens=0)) == ()


def test_a_badge_is_a_shields_image():
    assert badges.shield("🧹 Clean Coder", 3) == (
        "![🧹 Clean Coder +3](https://img.shields.io/badge/"
        "%F0%9F%A7%B9%20Clean%20Coder-%2B3%20pts-1f6feb?style=for-the-badge)"
    )
