"""Règle 5 : un échec métier est-il une valeur, ou une exception ?

Tout `raise` dans le modèle (`domain/model`, et `anemic_model` tant que la règle 3 n'est pas faite) est un constat
(FV001). Pour commencer, aucune exception n'est tolérée. L'échec se rend en valeur : `withdraw` rend
`Withdrawn | InsufficientStock`, et l'appelant le traite (`match` exhaustif, vérifié par pyright).

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`.
"""

import ast
from dataclasses import dataclass

from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage

CODE = "FV001"


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    col: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}:{self.col}: {self.code} {self.message}"


def check(source: Source, language: UbiquitousLanguage) -> list[Finding]:
    """Un constat par `raise` du fichier, dans l'ordre des lignes."""
    raises = sorted(
        (node for node in ast.walk(source.tree) if isinstance(node, ast.Raise)),
        key=lambda node: (node.lineno, node.col_offset),
    )
    return [
        Finding(
            path=source.path,
            line=node.lineno,
            col=node.col_offset + 1,
            code=CODE,
            message="`raise` dans le modèle : rendre l'échec comme valeur",
        )
        for node in raises
    ]
