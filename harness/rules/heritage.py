"""Règle 4 : les variantes du modèle se composent-elles, ou héritent-elles les unes des autres ?

Une classe du modèle qui hérite d'une autre classe du même module (`PerishableProduct(Product)`) est un constat (HE001).
La variante se compose à la place : une union de dataclasses (`ShelfLife = Perishable | NonExpiring`), que `Product`
porte en un champ.

Les Enum, Protocol, TypedDict et exceptions sont exceptés. Une base déclarée dans un autre module (par exemple la
base SQLAlchemy `Base`) n'est pas vue : elle relève de la règle 3. Une règle travaille fichier par fichier, donc
l'héritage entre deux modules n'est pas vu non plus. Ce n'est pas une garantie, c'est un premier pas.

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`.
"""

import ast
from dataclasses import dataclass

from harness.rules.sources import Source, is_exempt_class, top_level_classes
from harness.rules.ubiquitous_language import UbiquitousLanguage

CODE = "HE001"


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    col: int
    cls: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}:{self.col}: {self.code} {self.message}"


def check(source: Source, language: UbiquitousLanguage) -> list[Finding]:
    """Un constat par base déclarée dans le même module, quand la classe et la base ne sont pas exceptées."""
    classes = {cls.name: cls for cls in top_level_classes(source.tree)}
    findings: list[Finding] = []
    for cls in classes.values():
        if is_exempt_class(cls):
            continue
        for base in _base_names(cls):
            parent = classes.get(base)
            if parent is None or is_exempt_class(parent):
                continue
            findings.append(
                Finding(
                    path=source.path,
                    line=cls.lineno,
                    col=cls.col_offset + 1,
                    cls=cls.name,
                    code=CODE,
                    message=(
                        f"`{cls.name}` hérite de `{base}` : la variante se compose "
                        "(union de dataclasses, champ dans la classe qui la porte)"
                    ),
                )
            )
    return findings


def _base_names(cls: ast.ClassDef) -> list[str]:
    return [base.id for base in cls.bases if isinstance(base, ast.Name)]
