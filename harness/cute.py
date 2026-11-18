"""Les jauges CUTE : quatre chiffres de 0 à 100 qui résument les règles et les métriques du harnais.

`uv run python -m harness.cute [--src-root src] [--mutation-stats stats.json]` affiche les jauges du code courant.
`uv run python -m harness.cute --figer` réécrit la référence du legacy (`cute_reference.json`) à partir du code courant :
à ne lancer que sur le code de départ de l'atelier.

Une jauge dit quelle part du chemin est faite depuis le legacy : le legacy vaut 0, une règle verte vaut 100. Les
formules et leurs raisons sont dans docs/CUTE.md. Les jauges guident : elles ne rapportent aucun point.
"""

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from harness import mutation
from harness.metrics.__main__ import DEFAULT_ROOTS
from harness.metrics.report import Metrics
from harness.perimetre import dossiers_exclus
from harness.rules import RULES
from harness.rules import evaluate as evaluate_rules
from harness.rules.contexte_borne import coverage as member_coverage
from harness.rules.sources import collect
from harness.rules.ubiquitous_language import UbiquitousLanguage

REFERENCE_PATH = Path(__file__).with_name("cute_reference.json")
# La violation du sens des dépendances plafonne 🗺️ : une flèche à l'envers casse les frontières.
CONTEXTUAL_CAP_WITH_VIOLATION = 50
# Simplicité : 1 quand la pire fonction a au plus 4 chemins, 0 à partir de 10.
SIMPLE_CYCLOMATIC = 4
COMPLEX_CYCLOMATIC = 10


@dataclass(frozen=True)
class Reference:
    """Le point de départ : les constats de chaque règle et les attributs mutables du code legacy."""

    findings: Mapping[int, int]
    mutable_attributes: int

    @classmethod
    def load(cls, path: Path = REFERENCE_PATH) -> "Reference":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            findings={int(rule): int(count) for rule, count in data["findings"].items()},
            mutable_attributes=int(data["mutable_attributes"]),
        )

    def to_json(self) -> str:
        return (
            json.dumps(
                {
                    "//": "Le legacy de l'atelier, figé par `python -m harness.cute --figer`. Voir docs/CUTE.md.",
                    "findings": {str(rule): count for rule, count in sorted(self.findings.items())},
                    "mutable_attributes": self.mutable_attributes,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )


@dataclass(frozen=True)
class State:
    """Ce que les jauges lisent d'un état du code.

    `findings` : le nombre de constats par règle. Une règle absente (son dossier n'existe plus) n'a pas de constat.
    `mutation` : le score de mutation en %, `None` quand on ne le connaît pas.
    `coverage` : la part des membres non génériques rattachés à un contexte, `None` quand aucun membre ne compte.
    """

    findings: Mapping[int, int]
    metrics: Metrics
    mutation: float | None = None
    coverage: float | None = None


@dataclass(frozen=True)
class Gauges:
    contextual: int
    ubiquitous: int
    testable: int
    expressive: int


# (emoji, nom, attribut de `Gauges`), dans l'ordre de l'acronyme.
LETTERS = (
    ("🗺️", "Contextual", "contextual"),
    ("🗣️", "Ubiquitous", "ubiquitous"),
    ("🧪", "Testable", "testable"),
    ("📖", "Expressive", "expressive"),
)


def progress(now: int, legacy: int) -> float:
    """La part du chemin faite : 0 au niveau du legacy (ou pire), 1 sans constat."""
    if now <= 0:
        return 1.0
    if legacy <= 0:
        return 0.0
    return max(0.0, min(1.0, 1 - now / legacy))


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def gauges(state: State, reference: Reference) -> Gauges:
    def rule(number: int) -> float:
        return progress(state.findings.get(number, 0), reference.findings.get(number, 0))

    m = state.metrics

    contextual = 0.6 * rule(1) + 0.4 * (1 - _clamp(m.uncle_bob))
    if m.stability_violations > 0:
        contextual = min(contextual, CONTEXTUAL_CAP_WITH_VIOLATION / 100)

    ubiquitous = rule(2) if state.coverage is None else 0.5 * rule(2) + 0.5 * state.coverage

    simplicity = _clamp(
        (COMPLEX_CYCLOMATIC - m.max_cyclomatic) / (COMPLEX_CYCLOMATIC - SIMPLE_CYCLOMATIC)
    )
    isolation = _mean([rule(3), rule(6), rule(10)])
    testable = (
        0.5 * isolation + 0.5 * simplicity
        if state.mutation is None
        else 0.4 * _clamp(state.mutation / 100) + 0.3 * isolation + 0.3 * simplicity
    )

    immutability = progress(m.mutable_attributes, reference.mutable_attributes)
    expressive = (
        0.4 * _mean([rule(5), rule(7)])
        + 0.3 * _mean([rule(4), rule(8), rule(9)])
        + 0.3 * immutability
    )

    return Gauges(
        contextual=_percent(contextual),
        ubiquitous=_percent(ubiquitous),
        testable=_percent(testable),
        expressive=_percent(expressive),
    )


def _percent(value: float) -> int:
    return round(_clamp(value) * 100)


def coverage(src_root: Path, language: UbiquitousLanguage | None = None) -> float | None:
    """La couverture de l'ubiquitous language, sur le périmètre de la règle 1."""
    language = language or UbiquitousLanguage.load()
    rule = next(r for r in RULES if r.number == 1)
    roots = [src_root / root for root in rule.roots if (src_root / root).is_dir()]
    sources = collect(roots, src_root, dossiers_exclus(src_root, rule.hors))
    counts = [member_coverage(source, language) for source in sources]
    counted = sum(c for _, c in counts)
    return sum(a for a, _ in counts) / counted if counted else None


def state_of(
    src_root: Path,
    metrics: Metrics,
    findings: Mapping[int, Sequence[object]],
    mutation_score: float | None = None,
) -> State:
    return State(
        findings={rule: len(found) for rule, found in findings.items()},
        metrics=metrics,
        mutation=mutation_score,
        coverage=coverage(src_root),
    )


def section(head: Gauges, base: Gauges | None, mutation_known: bool = True) -> str:
    """La section « CUTE » de la scorecard : une ligne par jauge, base → PR."""
    lines = ["### 🌈 CUTE", "", "```"]
    for emoji, name, attr in LETTERS:
        now: int = getattr(head, attr)
        before: int | None = None if base is None else getattr(base, attr)
        lines.append(f"{emoji} {name:<11} {_values(before, now):<16} {_bar(now)}")
    lines += ["```", ""]
    note = (
        "0 = le code legacy, 100 = le chemin fait. Les jauges guident, sans points. "
        "Le calcul est dans `docs/CUTE.md`."
    )
    if not mutation_known:
        note += " 🧪 est calculée sans score de mutation."
    lines += [f"<sub>{note}</sub>", ""]
    return "\n".join(lines)


def _values(before: int | None, now: int) -> str:
    if before is None:
        return f"{now:>3}"
    change = now - before
    delta = f"  ({change:+d})" if change else ""
    return f"{before:>3} → {now:>3}{delta}"


def _bar(value: int, width: int = 10) -> str:
    filled = round(value / 100 * width)
    return "█" * filled + "░" * (width - filled)


def main() -> None:
    from harness.scorecard import measure_tree

    parser = argparse.ArgumentParser(
        prog="harness.cute", description="Les jauges CUTE du code courant."
    )
    parser.add_argument("--src-root", default="src")
    parser.add_argument("--mutation-stats", help="statistiques mutmut (`mutmut export-cicd-stats`)")
    parser.add_argument(
        "--figer",
        action="store_true",
        help="réécrit la référence du legacy à partir du code courant",
    )
    args = parser.parse_args()
    src_root = Path(args.src_root)
    metrics = measure_tree(src_root, [root.removeprefix("src/") for root in DEFAULT_ROOTS])
    findings = evaluate_rules(src_root)
    if args.figer:
        reference = Reference(
            findings={rule: len(found) for rule, found in findings.items()},
            mutable_attributes=metrics.mutable_attributes,
        )
        REFERENCE_PATH.write_text(reference.to_json(), encoding="utf-8")
        print(f"Référence écrite dans {REFERENCE_PATH}")
        return
    score = mutation.score(args.mutation_stats)
    state = state_of(src_root, metrics, findings, score)
    print(section(gauges(state, Reference.load()), None, score is not None))


if __name__ == "__main__":
    main()
