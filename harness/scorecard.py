"""La scorecard d'une PR : les mesures du code de la PR, comparées à celles de sa base.

`uv run python -m harness.scorecard --base-ref origin/main [--output scorecard.md]`

La CI la publie en commentaire de PR. Elle guide et chiffre : les points des règles, et un bonus ou un malus
pour chaque variation des métriques marquées `scored`. L'arbitre viendra plus tard.
"""

import argparse
import difflib
import io
import subprocess
import tarfile
import tempfile
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from harness import badges, mutation
from harness.metrics import tokens
from harness.metrics.__main__ import DEFAULT_ROOTS
from harness.metrics.martin import LayerMetrics
from harness.metrics.report import ClassMetrics, Metrics, measure
from harness.metrics.sources import collect
from harness.perimetre import description, dossiers_exclus
from harness.rules import evaluate as evaluate_rules
from harness.rules import report as rules_report
from harness.rules import results as rule_results
from harness.rules.points import metric_points

MARKER = "<!-- harness-scorecard -->"
TOP_CLASSES = 3


@dataclass(frozen=True)
class Row:
    """Une ligne du tableau. `better` dit dans quel sens aller : -1 pour « moins c'est mieux », +1 pour l'inverse.

    `scored` : la variation de cette ligne rapporte ou retire des points (voir `metric_lines`).
    `weight` : l'importance de la ligne dans le score. 1 par défaut, 0 pour neutraliser la mesure.
    """

    label: str
    read: Callable[[Metrics], float]
    better: int
    scored: bool = False
    weight: float = 1.0


ROWS = (
    Row("Tokens", lambda m: m.tokens, -1),
    Row("Complexité cyclomatique (total)", lambda m: m.cyclomatic, -1),
    Row(
        "Complexité cyclomatique (max par fonction)",
        lambda m: m.max_cyclomatic,
        -1,
        scored=True,
        weight=2,
    ),
    Row("WMC (pire classe)", lambda m: m.max_wmc, -1, scored=True, weight=0),
    Row("Complexité cognitive (total)", lambda m: m.cognitive, -1),
    Row("TCC (pire classe, 1 = cohésive)", lambda m: m.min_tcc, +1, scored=True, weight=0),
    Row("LCOM* (pire classe, 0 = cohésive)", lambda m: m.max_lcom, -1, scored=True, weight=0),
    Row("Fan-out (pire classe)", lambda m: m.max_fan_out, -1, scored=True, weight=1),
    # Remplace les totaux de fan-out et de CBO : le couplage entre couches, dans le sens des liens (0 = le mieux).
    # D varie par dixièmes : le poids 10 fait valoir 1 point à une variation de 0,1.
    Row(
        "Métrique Uncle Bob (D moyen des couches, 0 = le mieux)",
        lambda m: m.uncle_bob,
        -1,
        scored=True,
        weight=10,
    ),
    # Le sens de chaque lien, que D ne voit pas : une violation ajoutée coûte 1 point.
    Row(
        "Violations du sens des dépendances (vers plus instable)",
        lambda m: m.stability_violations,
        -1,
        scored=True,
        weight=1,
    ),
    Row("CBO (pire classe)", lambda m: m.max_cbo, -1, scored=True, weight=1),
    Row("Attributs mutables", lambda m: m.mutable_attributes, -1, scored=True, weight=1),
    Row("Affectations", lambda m: m.assignments, -1, scored=True, weight=0),
    Row("Boucles", lambda m: m.loops, -1, scored=True, weight=0),
    # Toutes les lambdas : un thermomètre, sans points. `map(lambda ...)` sur une liste ne doit rien rapporter.
    Row("Lambdas", lambda m: m.lambdas, +1, scored=True, weight=0),
    # Les lambdas qui sont une étape des rails d'un `Result` (règle 9, ROP) : elles seules rapportent.
    Row("Lambdas sur les rails (ROP)", lambda m: m.rail_lambdas, +1, scored=True, weight=1),
)


def render(
    head: Metrics,
    base: Metrics | None,
    changed_tokens: int | None = None,
    rules_md: str = "",
    mutation: tuple[float | None, float | None] = (None, None),
    badges_md: str = "",
) -> str:
    """`mutation` : le score de mutation (en %) de la base et de la PR, quand la CI les fournit.

    `badges_md` : la section des badges gagnés, affichée en tête du commentaire.
    """
    lines = [
        MARKER,
        "## 📊 Scorecard du harnais",
        "",
        "Des **repères pour guider ton refactoring**  "
        "Le détail de chaque chiffre est dans `docs/METRIQUES.md`.",
        "",
        *([badges_md] if badges_md else []),
        *([rules_md] if rules_md else []),
        "### 📏 Métriques",
        "",
        "| Mesure | Base | PR | Variation | |",
        "|---|---:|---:|---:|:--:|",
        *(_row(row, head, base) for row in ROWS),
    ]
    if changed_tokens is not None:
        lines.append(
            f"| Tokens modifiés par la PR | | {changed_tokens} | | {_small_diff(changed_tokens)} |"
        )
    lines += _mutation_row(*mutation)
    lines += ["", *_worst_classes(head), "", *_layers(head, base), ""]
    lines.append(
        f"<sub>Périmètre : {description()}. ✅ s'améliore, ⚠️ se dégrade, · inchangé.</sub>"
        if base
        else "<sub>Pas de base comparable : seules les valeurs de la PR sont affichées.</sub>"
    )
    return "\n".join(lines) + "\n"


def _row(row: Row, head: Metrics, base: Metrics | None) -> str:
    now = row.read(head)
    if base is None:
        return f"| {row.label} | | {_fmt(now)} | | |"
    before = row.read(base)
    return f"| {row.label} | {_fmt(before)} | {_fmt(now)} | {_delta(now - before)} | {_verdict(now - before, row.better)} |"


def metric_lines(head: Metrics, base: Metrics | None) -> tuple[tuple[str, int], ...]:
    """Les points des métriques : (libellé, points) pour chaque ligne `scored` qui a une base à comparer.

    Une ligne de poids 0 ne rapporte jamais rien : elle reste dans le tableau des mesures, pas dans celui des points.
    """
    if base is None:
        return ()
    return tuple(
        (row.label, metric_points(row.read(head) - row.read(base), row.better, row.weight))
        for row in ROWS
        if row.scored and row.weight
    )


def _fmt(value: float) -> str:
    return f"{value:g}"


def _delta(change: float) -> str:
    return "" if change == 0 else f"{change:+.2f}".rstrip("0").rstrip(".")


def _verdict(change: float, better: int) -> str:
    if change == 0:
        return "·"
    return "✅" if change * better > 0 else "⚠️"


def _mutation_row(base: float | None, head: float | None) -> list[str]:
    label = "Score de mutation (modèle, % de mutants tués)"
    if head is None:
        return []
    if base is None:
        return [f"| {label} | | {_fmt(head)} | | |"]
    change = head - base
    return [
        f"| {label} | {_fmt(base)} | {_fmt(head)} | {_delta(round(change, 1))} | {_verdict(change, +1)} |"
    ]


def _small_diff(changed_tokens: int) -> str:
    if changed_tokens == 0:
        return "🫥 PR vide"
    return "🤏 Small diff" if changed_tokens <= badges.SMALL_DIFF_TOKENS else ""


def _worst_classes(head: Metrics) -> list[str]:
    """Là où regarder en premier : les classes les plus couplées, puis les plus complexes."""
    ranked = sorted(head.per_class, key=lambda c: (-c.cbo, -c.wmc, c.name))[:TOP_CLASSES]
    if not ranked:
        return ["_Aucune classe mesurée._"]
    return [
        "**Où regarder en premier** (les classes les plus couplées) :",
        "",
        "| Classe | CBO | Fan-out | WMC | Cognitive | TCC | LCOM* |",
        "|---|---:|---:|---:|---:|---:|---:|",
        *(_class_row(c) for c in ranked),
    ]


def _class_row(c: ClassMetrics) -> str:
    tcc = "n/a" if c.tcc is None else _fmt(c.tcc)
    lcom = "n/a" if c.lcom is None else _fmt(c.lcom)
    return f"| `{c.name}` | {c.cbo} | {c.fan_out} | {c.wmc} | {c.cognitive} | {tcc} | {lcom} |"


def _layers(head: Metrics, base: Metrics | None) -> list[str]:
    """Les métriques de Martin par couche, base → PR. Elles guident : elles ne rapportent pas de points."""
    if not head.layers:
        return []
    before = {layer.name: layer for layer in base.layers} if base else {}
    return [
        "**Les couches** (Robert Martin : I instabilité, A abstraction, D distance à la séquence principale, "
        "0 est le mieux) :",
        "",
        "| Couche | Ca | Ce | I | A | D | Dépend de |",
        "|---|---:|---:|---:|---:|---:|---|",
        *(_layer_row(layer, before.get(layer.name)) for layer in head.layers),
    ]


_LAYER_COLUMNS = ("afferent", "efferent", "instability", "abstractness", "distance")


def _layer_row(now: LayerMetrics, then: LayerMetrics | None) -> str:
    cells = [_change(then, now, column) for column in _LAYER_COLUMNS]
    depends = ", ".join(f"`{name}`" for name in now.depends_on) or "—"
    return f"| `{now.name}` | {' | '.join(cells)} | {depends} |"


def _change(then: LayerMetrics | None, now: LayerMetrics, column: str) -> str:
    """La valeur de la PR, précédée de celle de la base quand la couche y existait et que la valeur a changé."""
    after: float | None = getattr(now, column)
    if then is None:
        return _shown(after)
    before: float | None = getattr(then, column)
    return _shown(after) if before == after else f"{_shown(before)} → {_shown(after)}"


def _shown(value: float | None) -> str:
    return "n/a" if value is None else _fmt(value)


def measure_tree(src_root: Path, roots: list[str]) -> Metrics:
    return measure(
        collect([src_root / root for root in roots], src_root, dossiers_exclus(src_root))
    )


@contextmanager
def checkout(ref: str) -> Generator[Path | None]:
    """Le dossier `src` tel qu'il est à `ref` (sans toucher à l'arbre de travail) ; `None` s'il n'y existe pas.

    `tests` est extrait à côté, quand il existe : la règle 6 y lit les `patch`.
    """
    archive = _archive(ref, "src")
    if archive is None:
        yield None
        return
    with tempfile.TemporaryDirectory() as tmp:
        for content in (archive, _archive(ref, "tests")):
            if content is not None:
                with tarfile.open(fileobj=io.BytesIO(content)) as tar:
                    tar.extractall(tmp, filter="data")
        yield Path(tmp) / "src"


def _archive(ref: str, folder: str) -> bytes | None:
    result = subprocess.run(["git", "archive", ref, folder], check=False, capture_output=True)
    return result.stdout if result.returncode == 0 else None


def _relative_to_src(root: str) -> str:
    return root.removeprefix("src/")


def _effective_lines(src_root: Path, roots: list[str]) -> dict[str, list[str]]:
    return {
        source.module: tokens.effective_code(source.tree).splitlines()
        for source in collect(
            [src_root / root for root in roots], src_root, dossiers_exclus(src_root)
        )
    }


def changed_tokens(base_src: Path, head_src: Path, roots: list[str]) -> int:
    """Les tokens du code efficace ajouté ou retiré dans le périmètre (ni commentaires, ni docstrings, ni mise en forme)."""
    before = _effective_lines(base_src, roots)
    after = _effective_lines(head_src, roots)
    changed = [
        line[1:]
        for module in sorted(before.keys() | after.keys())
        for line in difflib.unified_diff(
            before.get(module, []), after.get(module, []), n=0, lineterm=""
        )
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    ]
    return tokens.count("\n".join(changed))


def main() -> None:
    parser = argparse.ArgumentParser(prog="harness.scorecard", description="Scorecard d'une PR.")
    parser.add_argument("--base-ref", help="référence git de comparaison (ex. origin/main)")
    parser.add_argument(
        "--output", help="écrit la scorecard dans ce fichier (sinon, sur la sortie)"
    )
    parser.add_argument(
        "--mutation-stats", help="statistiques mutmut de la PR (`mutmut export-cicd-stats`)"
    )
    parser.add_argument(
        "--base-mutation-stats", help="statistiques mutmut de la base (dernier passage sur main)"
    )
    parser.add_argument("roots", nargs="*", default=list(DEFAULT_ROOTS))
    args = parser.parse_args()
    head = measure_tree(Path("src"), [_relative_to_src(root) for root in args.roots])
    roots = [_relative_to_src(root) for root in args.roots]
    head_findings = evaluate_rules(Path("src"))
    base_findings = None
    if args.base_ref:
        with checkout(args.base_ref) as base_src:
            base = None if base_src is None else measure_tree(base_src, roots)
            changed = None if base_src is None else changed_tokens(base_src, Path("src"), roots)
            base_findings = None if base_src is None else evaluate_rules(base_src)
    else:
        base, changed = None, None
    results = rule_results(head_findings, base_findings)
    metrics = metric_lines(head, base)
    scores = (mutation.score(args.base_mutation_stats), mutation.score(args.mutation_stats))
    pr = (
        None
        if base is None or changed is None
        else badges.Pr(head, base, changed, results, metrics, *scores)
    )
    rules_md = rules_report.section(results, metrics, changed, badges.lines(pr))
    card = render(head, base, changed, rules_md, scores, badges.banner(badges.won(pr)))
    if args.output:
        Path(args.output).write_text(card, encoding="utf-8")
    else:
        print(card)


if __name__ == "__main__":
    main()
