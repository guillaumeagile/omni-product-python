"""La scorecard d'une PR : les mesures du code de la PR, comparées à celles de sa base.

`uv run python -m harness.scorecard --base-ref origin/main [--output scorecard.md]`

La CI la publie en commentaire de PR. Elle guide, elle ne note pas : l'arbitre viendra plus tard.
"""

import argparse
import io
import subprocess
import tarfile
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from harness.metrics import tokens
from harness.metrics.__main__ import DEFAULT_ROOTS
from harness.metrics.report import ClassMetrics, Metrics, measure
from harness.metrics.sources import collect

MARKER = "<!-- harness-scorecard -->"
TOP_CLASSES = 3


@dataclass(frozen=True)
class Row:
    """Une ligne du tableau. `better` dit dans quel sens aller : -1 pour « moins c'est mieux », +1 pour l'inverse."""

    label: str
    read: Callable[[Metrics], float]
    better: int


ROWS = (
    Row("Tokens", lambda m: m.tokens, -1),
    Row("Complexité cyclomatique (total)", lambda m: m.cyclomatic, -1),
    Row("Complexité cyclomatique (max par fonction)", lambda m: m.max_cyclomatic, -1),
    Row("WMC (pire classe)", lambda m: m.max_wmc, -1),
    Row("Complexité cognitive (total)", lambda m: m.cognitive, -1),
    Row("Complexité cognitive (max par fonction)", lambda m: m.max_cognitive, -1),
    Row("TCC (pire classe, 1 = cohésive)", lambda m: m.min_tcc, +1),
    Row("LCOM* (pire classe, 0 = cohésive)", lambda m: m.max_lcom, -1),
    Row("Fan-out (total)", lambda m: m.fan_out, -1),
    Row("Fan-out (pire classe)", lambda m: m.max_fan_out, -1),
    Row("CBO (total)", lambda m: m.cbo, -1),
    Row("CBO (pire classe)", lambda m: m.max_cbo, -1),
    Row("Attributs mutables", lambda m: m.mutable_attributes, -1),
    Row("Affectations", lambda m: m.assignments, -1),
    Row("Boucles", lambda m: m.loops, -1),
    Row("Lambdas", lambda m: m.lambdas, +1),
)


def render(head: Metrics, base: Metrics | None, changed_tokens: int | None = None) -> str:
    lines = [
        MARKER,
        "## 📊 Scorecard du harnais",
        "",
        "Des **repères pour guider ton refactoring**, pas une note : un thermomètre, pas un objectif. "
        "Le détail de chaque chiffre est dans `docs/METRIQUES.md`.",
        "",
        "| Mesure | Base | PR | Variation | |",
        "|---|---:|---:|---:|:--:|",
        *(_row(row, head, base) for row in ROWS),
    ]
    if changed_tokens is not None:
        lines.append(
            f"| Tokens modifiés par la PR | | {changed_tokens} | | {_small_diff(changed_tokens)} |"
        )
    lines += ["", *_worst_classes(head), ""]
    lines.append(
        "<sub>Périmètre : `model/` et `service/`. ✅ s'améliore, ⚠️ se dégrade, · inchangé.</sub>"
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


def _fmt(value: float) -> str:
    return f"{value:g}"


def _delta(change: float) -> str:
    return "" if change == 0 else f"{change:+.2f}".rstrip("0").rstrip(".")


def _verdict(change: float, better: int) -> str:
    if change == 0:
        return "·"
    return "✅" if change * better > 0 else "⚠️"


def _small_diff(changed_tokens: int) -> str:
    return "🤏 Small diff" if changed_tokens <= 400 else ""


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


def measure_tree(src_root: Path, roots: list[str]) -> Metrics:
    return measure(collect([src_root / root for root in roots], src_root))


def measure_ref(ref: str, roots: list[str]) -> Metrics | None:
    """Mesure le code tel qu'il est à `ref` (sans toucher à l'arbre de travail) ; `None` si le périmètre n'y existe pas."""
    archive = subprocess.run(["git", "archive", ref, "src"], check=False, capture_output=True)
    if archive.returncode != 0:
        return None
    with (
        tempfile.TemporaryDirectory() as tmp,
        tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar,
    ):
        tar.extractall(tmp, filter="data")
        return measure_tree(Path(tmp) / "src", [_relative_to_src(root) for root in roots])


def _relative_to_src(root: str) -> str:
    return root.removeprefix("src/")


def changed_tokens(ref: str, roots: list[str]) -> int:
    """Les tokens des lignes ajoutées ou retirées dans le périmètre, entre `ref` et le code actuel."""
    diff = subprocess.run(
        ["git", "diff", "--unified=0", ref, "--", *roots],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    changed = [
        line[1:]
        for line in diff.splitlines()
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    ]
    return tokens.count("\n".join(changed))


def main() -> None:
    parser = argparse.ArgumentParser(prog="harness.scorecard", description="Scorecard d'une PR.")
    parser.add_argument("--base-ref", help="référence git de comparaison (ex. origin/main)")
    parser.add_argument(
        "--output", help="écrit la scorecard dans ce fichier (sinon, sur la sortie)"
    )
    parser.add_argument("roots", nargs="*", default=list(DEFAULT_ROOTS))
    args = parser.parse_args()
    head = measure_tree(Path("src"), [_relative_to_src(root) for root in args.roots])
    base = measure_ref(args.base_ref, args.roots) if args.base_ref else None
    changed = changed_tokens(args.base_ref, args.roots) if base and args.base_ref else None
    card = render(head, base, changed)
    if args.output:
        Path(args.output).write_text(card, encoding="utf-8")
    else:
        print(card)


if __name__ == "__main__":
    main()
