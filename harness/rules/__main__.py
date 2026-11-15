"""`uv run python -m harness.rules [--json rapport.json] [--markdown rapport.md] [dossiers...]`.

Lance les règles maison sur le code. Non bloquant : le script sort toujours en 0, les violations sont des chiffres
pour la scorecard, pas un échec de CI.
"""

import argparse
import json
from pathlib import Path

from harness.rules import contexte_borne
from harness.rules.contexte_borne import Violation
from harness.rules.sources import collect
from harness.rules.vocabulary import Vocabulary

DEFAULT_ROOTS = ("src/omni_product/anemic_model",)


def render_markdown(violations: list[Violation]) -> str:
    lines = [
        "### Règles maison (harnais)",
        "",
        f"- Règle 1, contexte borné : **{len(violations)}** classe(s) à éclater",
    ]
    lines.extend(f"  - `{v.cls}` ({v.module}:{v.line}) touche {' + '.join(v.members_by_concern)}" for v in violations)
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="harness.rules", description="Règles de design maison de l'atelier (non bloquantes)."
    )
    parser.add_argument("roots", nargs="*", default=list(DEFAULT_ROOTS), help="dossiers à analyser")
    parser.add_argument("--src-root", default="src", help="racine des imports (défaut : src)")
    parser.add_argument("--json", dest="json_path", help="écrit le rapport détaillé dans ce fichier")
    parser.add_argument("--markdown", dest="markdown_path", help="écrit le bloc Markdown de la scorecard")
    args = parser.parse_args()

    sources = collect([Path(root) for root in args.roots], Path(args.src_root))
    vocabulary = Vocabulary.load()
    violations = [v for source in sources for v in contexte_borne.check(source, vocabulary)]

    print(f"Règle 1, contexte borné : {len(violations)} classe(s) à éclater")
    for violation in violations:
        print(f"  {violation}")

    if args.json_path:
        report = {
            "rules": {
                "contexte_borne": {
                    "violations": len(violations),
                    "classes": [
                        {
                            "module": v.module,
                            "class": v.cls,
                            "line": v.line,
                            "members_by_concern": v.members_by_concern,
                        }
                        for v in violations
                    ],
                }
            }
        }
        Path(args.json_path).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    if args.markdown_path:
        Path(args.markdown_path).write_text(render_markdown(violations), encoding="utf-8")


if __name__ == "__main__":
    main()
