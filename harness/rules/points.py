"""Le barème des règles : ce qu'une PR gagne en points, à partir des constats avant et après.

Même barème que l'arbitre de l'atelier Java :
- +10 par règle passée au vert par la PR ;
- +1 par constat retiré sur une règle encore rouge, plafonné à +5 au total ;
- +5 de « baby step » quand une seule règle passe au vert ;
- ±1 par variation de métrique (dans le bon ou le mauvais sens), net, plafonné à ±10.

Une règle qui repasse du vert au rouge ne fait pas perdre de points, mais la scorecard la signale.
"""

from collections.abc import Sequence
from dataclasses import dataclass

TURNED_GREEN_POINTS = 10
REMOVED_ON_RED_CAP = 5
BABY_STEP_POINTS = 5
METRIC_CAP = 10


@dataclass(frozen=True)
class RuleResult:
    number: int
    title: str
    # `None` quand il n'y a pas de base comparable (scorecard sur `main` seul).
    before: int | None
    after: int

    @property
    def turned_green(self) -> bool:
        return self.before is not None and self.before > 0 and self.after == 0

    @property
    def regressed(self) -> bool:
        return self.before == 0 and self.after > 0

    @property
    def still_red(self) -> bool:
        return self.before is not None and self.before > 0 and self.after > 0

    @property
    def removed(self) -> int:
        """Les constats retirés sur une règle encore rouge : ce qui rapporte des points de réduction."""
        if self.before is None or not self.still_red:
            return 0
        return max(0, self.before - self.after)


@dataclass(frozen=True)
class Score:
    results: tuple[RuleResult, ...]
    green_points: int
    removed_points: int
    baby_step_points: int
    metric_points: int = 0

    @property
    def total(self) -> int:
        return self.green_points + self.removed_points + self.baby_step_points + self.metric_points

    @property
    def turned_green(self) -> tuple[RuleResult, ...]:
        return tuple(r for r in self.results if r.turned_green)

    @property
    def regressed(self) -> tuple[RuleResult, ...]:
        return tuple(r for r in self.results if r.regressed)


def metric_bonus(steps: Sequence[int]) -> int:
    """Le bonus des métriques : chaque variation vaut +1 (amélioration) ou -1 (dégradation), net, plafonné à ±METRIC_CAP."""
    return max(-METRIC_CAP, min(METRIC_CAP, sum(steps)))


def score(results: tuple[RuleResult, ...], metric_steps: Sequence[int] = ()) -> Score:
    green = [r for r in results if r.turned_green]
    removed = sum(r.removed for r in results)
    return Score(
        results=results,
        green_points=TURNED_GREEN_POINTS * len(green),
        removed_points=min(REMOVED_ON_RED_CAP, removed),
        baby_step_points=BABY_STEP_POINTS if len(green) == 1 else 0,
        metric_points=metric_bonus(metric_steps),
    )
