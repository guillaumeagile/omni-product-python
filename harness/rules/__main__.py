"""`uv run python -m harness.rules [--src-root src] [--json rapport.json]`.

Liste les constats de chaque règle du registre, pour le code courant. Non bloquant : le script sort toujours en 0.
La table de la scorecard (avec les points, comparée à une base) s'obtient avec
`uv run python -m harness.scorecard --base-ref origin/main`.
"""

import argparse
import json
from pathlib import Path

from harness.rules import RULES, evaluate


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="harness.rules", description="Règles de design maison de l'atelier (non bloquantes)."
    )
    parser.add_argument("--src-root", default="src", help="racine des imports (défaut : src)")
    parser.add_argument(
        "--json", dest="json_path", help="écrit le rapport détaillé dans ce fichier"
    )
    args = parser.parse_args()

    findings = evaluate(Path(args.src_root))
    # Comme ruff : une ligne par constat, puis le bilan ; « All checks passed! » quand tout est propre.
    count = 0
    for rule in RULES:
        for finding in findings[rule.number]:
            print(finding)
            count += 1
    if count:
        print(f"Found {count} warning{'s' if count > 1 else ''}.")
    else:
        print("All checks passed!")

    if args.json_path:
        report = {
            f"regle_{rule.number}": {
                "title": rule.title,
                "findings": [str(finding) for finding in findings[rule.number]],
            }
            for rule in RULES
        }
        Path(args.json_path).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
