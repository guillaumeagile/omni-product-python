"""Résumé Markdown du rapport mutmut, produit à partir de `mutmut export-cicd-stats`."""

import json
import sys
from pathlib import Path

MARKER = "<!-- mutation-report -->"


def render(stats: dict[str, int]) -> str:
    total = stats["total"]
    killed = stats["killed"]
    score = killed / total * 100 if total else 0.0
    rows = [
        ("Tués", killed),
        ("Survivants", stats["survived"]),
        ("Sans test", stats["no_tests"]),
        ("Timeout", stats["timeout"]),
        ("Suspects", stats["suspicious"]),
    ]
    lines = [
        MARKER,
        "### Mutation testing (modèle)",
        "",
        f"Score : **{score:.1f} %** ({killed} / {total} mutants tués)",
        "",
        "| Statut | Mutants |",
        "|---|---:|",
        *(f"| {label} | {count} |" for label, count in rows),
        "",
        "_Informatif : ce résultat n'est pas bloquant._",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    stats = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sys.stdout.write(render(stats))


if __name__ == "__main__":
    main()
