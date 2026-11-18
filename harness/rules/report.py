"""La section « Règles du harnais » de la scorecard : une ligne par règle, puis le score de la PR."""

from collections.abc import Sequence

from harness.rules.points import (
    METRIC_CAP,
    REMOVED_ON_RED_CAP,
    TURNED_GREEN_POINTS,
    RuleResult,
    score,
)


def section(
    results: tuple[RuleResult, ...],
    metric_lines: Sequence[tuple[str, int]] = (),
) -> str:
    result = score(results, metric_lines)
    has_base = any(r.before is not None for r in results)
    lines = [
        "### 🧪 Règles du harnais",
        "",
        "| Règle | Base | PR | Points |",
        "|---|---|---|---:|",
        *(_row(r) for r in results),
        "",
    ]
    if has_base:
        lines += [
            "| Score | Points |",
            "|---|---:|",
            *(
                f"| Règle {r.number} passée au vert 🎯 | +{TURNED_GREEN_POINTS} |"
                for r in result.turned_green
            ),
            f"| Constats retirés sur les règles encore rouges (plafond +{REMOVED_ON_RED_CAP}) | +{result.removed_points} |",
            f"| 🍼 Baby step : une seule règle passée au vert | +{result.baby_step_points} |",
            *(
                f"| Métrique : {label} (plafond ±{METRIC_CAP}) | {points:+d} |"
                for label, points in result.metric_lines
            ),
            f"| **Total** | **+{result.total}** |",
        ]
        lines += [
            f"\n⚠️ Régression sur la règle {r.number} : {r.before} → {r.after} constat(s)."
            for r in result.regressed
        ]
        lines.append("")
    else:
        lines += [
            "<sub>Pas de base comparable : seul l'état de la PR est affiché, sans points.</sub>",
            "",
        ]
    return "\n".join(lines)


def _row(r: RuleResult) -> str:
    base = "—" if r.before is None else _status(r.before)
    points = f"+{TURNED_GREEN_POINTS}" if r.turned_green else ""
    return f"| {r.number} · {r.title} | {base} | {_status(r.after)} | {points} |"


def _status(count: int) -> str:
    return "🟢 PASS" if count == 0 else f"🔴 FAIL ({count})"
