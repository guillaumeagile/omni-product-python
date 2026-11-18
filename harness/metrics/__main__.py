"""`uv run python -m harness.metrics [--json rapport.json] [dossiers...]`."""

import argparse
from pathlib import Path

from harness.metrics.report import Metrics, measure
from harness.metrics.sources import collect
from harness.perimetre import dossiers_exclus

DEFAULT_ROOTS = ("src/omni_product",)


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
        ("Fan-out max", metrics.max_fan_out),
        ("CBO max", metrics.max_cbo),
        ("Métrique Uncle Bob (D moyen des couches)", metrics.uncle_bob),
        ("Violations du sens des dépendances", metrics.stability_violations),
        ("Attributs mutables", metrics.mutable_attributes),
        ("Affectations", metrics.assignments),
        ("Boucles", metrics.loops),
        ("Lambdas", metrics.lambdas),
    ]
    return "\n".join(
        [f"{label:<52} {value}" for label, value in rows] + ["", *render_layers(metrics)]
    )


def render_layers(metrics: Metrics) -> list[str]:
    """Les métriques de Martin, une ligne par couche."""
    header = f"{'Couche':<16} {'Ca':>3} {'Ce':>3} {'I':>5} {'A':>5} {'D':>5}  Dépend de"
    return [
        header,
        *(
            f"{layer.name:<16} {layer.afferent:>3} {layer.efferent:>3} {_opt(layer.instability):>5} "
            f"{layer.abstractness:>5g} {_opt(layer.distance):>5}  {', '.join(layer.depends_on) or '—'}"
            for layer in metrics.layers
        ),
    ]


def _opt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:g}"


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
    src_root = Path(args.src_root)
    metrics = measure(
        collect([Path(root) for root in args.roots], src_root, dossiers_exclus(src_root))
    )
    print(render(metrics))
    if args.json_path:
        Path(args.json_path).write_text(metrics.to_json() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
