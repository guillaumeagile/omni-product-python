"""Les badges : de petits bonus qui saluent un geste précis de la PR.

Le badge 🍼 Baby step (une seule règle passée au vert) est dans le barème des règles (`harness.rules.points`). Ceux-ci
regardent les mesures. Un badge ne se gagne qu'avec une base à comparer, et jamais sur une PR vide.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from urllib.parse import quote

from harness.metrics.report import Metrics
from harness.rules.points import BABY_STEP_POINTS, RuleResult

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


def won(pr: Pr | None) -> tuple[tuple[str, int], ...]:
    """Tous les badges gagnés, 🍼 Baby step compris : ce qu'affiche l'en-tête du commentaire."""
    if pr is None or pr.changed_tokens == 0:
        return ()
    green = sum(result.turned_green for result in pr.results)
    baby_step = (("🍼 Baby step", BABY_STEP_POINTS),) if green == 1 else ()
    return baby_step + lines(pr)


def banner(won: Sequence[tuple[str, int]]) -> str:
    """La section des badges gagnés, en tête du commentaire. Vide quand la PR n'en gagne aucun."""
    if not won:
        return ""
    badges = " ".join(shield(label, points) for label, points in won)
    return f"### 🏅 Badges gagnés\n\n{badges}\n"


# La couleur de chaque badge sur shields.io.
COLORS = {
    "🍼 Baby step": "ff69b4",
    "🤏 Small diff": "0e8a16",
    "🧹 Clean Coder": "1f6feb",
    "✂️ Less is more": "8250df",
    "🧬 Tueur de mutants": "d1242f",
    "🧭 Uncle Bob approuve": "bf8700",
    "🧊 Immuable": "00a3c4",
}


def shield(label: str, points: int) -> str:
    """Un badge en image shields.io : le libellé à gauche, les points à droite."""
    url = (
        f"https://img.shields.io/badge/{_escape(label)}-{_escape(f'{points:+d} pts')}"
        f"-{COLORS.get(label, '555555')}?style=for-the-badge"
    )
    return f"![{label} {points:+d}]({url})"


def _escape(text: str) -> str:
    """Les tirets et soulignés sont doublés pour shields.io, le reste est encodé pour l'URL."""
    return quote(text.replace("-", "--").replace("_", "__"), safe="")
