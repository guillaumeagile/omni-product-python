"""Règle 3 : du code peut-il encore vivre dans `anemic_model/` ?

Le modèle se range dans `domain/model/`. Tout fichier non vide sous `anemic_model/` est un constat : tant qu'un fichier
y reste, la règle est rouge, et elle devient verte quand le dossier disparaît.

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`.
"""

from dataclasses import dataclass

from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage

CODE = "MA001"


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
    """Un constat par fichier non vide : son code doit être dans `omni_product/domain/model/`."""
    if not source.tree.body:
        return []
    return [
        Finding(
            path=source.path,
            line=1,
            col=1,
            code=CODE,
            message=f"`{source.module}` est dans anemic_model/ : le code du modèle va dans domain/model/",
        )
    ]
