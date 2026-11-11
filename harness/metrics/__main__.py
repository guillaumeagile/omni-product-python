"""`uv run python -m harness.metrics [--json rapport.json] [dossiers...]`."""

import argparse
from pathlib import Path

from harness.metrics.report import Metrics, measure
from harness.metrics.sources import collect

DEFAULT_ROOTS = ("src/omni_product/model", "src/omni_product/service")


def render(metrics: Metrics) -> str:
    rows = [
        ("Tokens (o200k_base)", metrics.tokens),
        ("Classes", metrics.classes),
        (
            "Complexité cyclomatique (total / max par fonction)",
            f"{metrics.cyclomatic} / {metrics.max_cyclomatic}",
        ),
        ("WMC max", metrics.max_wmc),
        (
            "Complexité cognitive (total / max par fonction)",
            f"{metrics.cognitive} / {metrics.max_cognitive}",
        ),
        ("TCC min", metrics.min_tcc),
        ("LCOM* max", metrics.max_lcom),
        ("Fan-out (total / max)", f"{metrics.fan_out} / {metrics.max_fan_out}"),
        ("CBO (total / max)", f"{metrics.cbo} / {metrics.max_cbo}"),
        ("Attributs mutables", metrics.mutable_attributes),
        ("Affectations", metrics.assignments),
        ("Boucles", metrics.loops),
        ("Lambdas", metrics.lambdas),
    ]
    return "\n".join(f"{label:<52} {value}" for label, value in rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="harness.metrics", description="Mesures du code de l'atelier."
    )
    parser.add_argument("roots", nargs="*", default=list(DEFAULT_ROOTS), help="dossiers à mesurer")
    parser.add_argument("--src-root", default="src", help="racine des imports (défaut : src)")
    parser.add_argument(
        "--json", dest="json_path", help="écrit le rapport détaillé dans ce fichier"
    )
    args = parser.parse_args()
    metrics = measure(collect([Path(root) for root in args.roots], Path(args.src_root)))
    print(render(metrics))
    if args.json_path:
        Path(args.json_path).write_text(metrics.to_json() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
