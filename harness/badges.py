"""Les badges : de petits bonus qui saluent un geste précis de la PR.

Le badge 🍼 Baby step (une seule règle passée au vert) est dans le barème des règles (`harness.rules.points`). Ceux-ci
regardent les mesures. Un badge ne se gagne qu'avec une base à comparer, et jamais sur une PR vide.
"""

from collections.abc import Callable
from dataclasses import dataclass

from harness.metrics.report import Metrics
from harness.rules.points import RuleResult

SMALL_DIFF_TOKENS = 400
CLEAN_CODER_POINTS = 5  # les points de métriques à atteindre pour 🧹 Clean Coder
UNCLE_BOB_STEP = 0.1  # la baisse de la métrique Uncle Bob qui vaut 🧭


@dataclass(frozen=True)
class Pr:
    """Ce qu'on sait d'une PR au moment de la noter."""

    head: Metrics
    base: Metrics
    changed_tokens: int
    results: tuple[RuleResult, ...] = ()
    metric_lines: tuple[tuple[str, int], ...] = ()
    # Le score de mutation (en %) de la base et de la PR, `None` quand on ne le connaît pas.
    base_mutation: float | None = None
    head_mutation: float | None = None


@dataclass(frozen=True)
class Badge:
    label: str
    reason: str
    points: int
    earned: Callable[[Pr], bool]


BADGES = (
    Badge(
        "🤏 Small diff",
        f"au plus {SMALL_DIFF_TOKENS} tokens de code modifiés",
        2,
        lambda pr: pr.changed_tokens <= SMALL_DIFF_TOKENS,
    ),
    Badge(
        "🧹 Clean Coder",
        f"les métriques rapportent au moins +{CLEAN_CODER_POINTS}",
        3,
        lambda pr: sum(points for _, points in pr.metric_lines) >= CLEAN_CODER_POINTS,
    ),
    Badge(
        "✂️ Less is more",
        "le code perd des tokens",
        2,
        lambda pr: pr.head.tokens < pr.base.tokens,
    ),
    Badge(
        "🧬 Tueur de mutants",
        "le score de mutation monte : les tests tuent une plus grande part des mutants",
        3,
        lambda pr: (
            pr.base_mutation is not None
            and pr.head_mutation is not None
            and pr.head_mutation > pr.base_mutation
        ),
    ),
    Badge(
        "🧭 Uncle Bob approuve",
        f"la métrique Uncle Bob baisse d'au moins {UNCLE_BOB_STEP}, sans violation du sens des dépendances en plus",
        3,
        lambda pr: (
            pr.base.uncle_bob - pr.head.uncle_bob >= UNCLE_BOB_STEP - 1e-9
            and pr.head.stability_violations <= pr.base.stability_violations
        ),
    ),
    Badge(
        "🧊 Immuable",
        "moins d'attributs mutables",
        2,
        lambda pr: pr.head.mutable_attributes < pr.base.mutable_attributes,
    ),
)


def earned(pr: Pr) -> tuple[Badge, ...]:
    """Les badges gagnés par la PR, dans l'ordre de `BADGES`. Une PR vide n'en gagne aucun."""
    if pr.changed_tokens == 0:
        return ()
    return tuple(badge for badge in BADGES if badge.earned(pr))


def lines(pr: Pr | None) -> tuple[tuple[str, int], ...]:
    """(libellé, points) de chaque badge gagné, pour le tableau des points."""
    return () if pr is None else tuple((badge.label, badge.points) for badge in earned(pr))
