"""Les badges, sur des PR dont on change une seule mesure à la fois."""

import textwrap
from dataclasses import replace

from harness import badges
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


def test_a_neutral_pr_only_earns_the_no_breakage_badge():
    assert labels(NEUTRAL) == ["🛡️ Sans casse"]


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


def test_a_regression_or_a_lost_metric_point_breaks_something():
    regressed = RuleResult(number=1, title="r", before=0, after=1)

    assert "🛡️ Sans casse" not in labels(replace(NEUTRAL, results=(regressed,)))
    assert "🛡️ Sans casse" not in labels(replace(NEUTRAL, metric_lines=(("a", 6), ("b", -1))))


def test_a_new_abstract_class_is_a_port():
    domain = BASE.layers[0]
    head = replace(BASE, layers=(replace(domain, abstract_classes=domain.abstract_classes + 1),))

    assert "🔌 Port" in labels(replace(NEUTRAL, head=head))


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
    assert "| Badge 🛡️ Sans casse | +2 |" in text
    assert "| **Total** | **+4** |" in text


def test_no_base_no_badge():
    assert badges.lines(None) == ()
