"""Règle 7 : un état illégal est-il impossible à construire ?

Trois indices disent qu'une classe du modèle (`domain/model`, et `anemic_model` tant que la règle 3 n'est pas faite)
laisse construire un état que le métier interdit :

- `EL001` : un champ booléen stocké, nommé `is_*` ou `has_*`. Le drapeau et les champs qu'il commande peuvent se
  contredire (`is_perishable=True` sans date). Chaque valeur du drapeau devient une variante d'une union fermée.
- `EL002` : plusieurs champs `X | None` dans la même classe. Ils vont le plus souvent par paires (une date et une
  durée, un nom et un identifiant) : la combinaison « l'un présent, l'autre absent » est illégale. Une variante par
  combinaison légale, et plus aucun `None`.
- `EL003` : un `raise` dans `__init__` ou `__post_init__`. L'invariant se vérifie à la construction, et l'objet
  incohérent existe une fraction de seconde. Une fabrique qui rend un résultat (`Ok(Perishable(...))` ou
  `Err(...)`) le valide avant que l'objet n'existe.

Le refactoring attendu est une union fermée de dataclasses frozen, par exemple `Perishable(sell_by, use_by)` ou
`NonExpiring(best_before)`, avec un `match` exhaustif vérifié par pyright.

Ce sont des heuristiques `ast`, sans garantie : elles voient la forme des champs, pas l'intention. Les annotations
`Mapped[X]` de SQLAlchemy sont lues comme `X`. Les énumérations, `Protocol`, `TypedDict` et exceptions sont exceptés,
comme pour les règles 2 et 4.

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`.
"""

import ast
from dataclasses import dataclass

from harness.rules.sources import Source, is_exempt_class
from harness.rules.ubiquitous_language import UbiquitousLanguage

CODE_FLAG = "EL001"
CODE_OPTIONALS = "EL002"
CODE_CONSTRUCTOR = "EL003"

FLAG_PREFIXES = ("is_", "has_")
CONSTRUCTORS = frozenset({"__init__", "__post_init__"})


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
    """Les constats du fichier, dans l'ordre des lignes."""
    findings: list[Finding] = []
    for cls in (node for node in ast.walk(source.tree) if isinstance(node, ast.ClassDef)):
        if is_exempt_class(cls):
            continue
        findings += _flags(source, cls)
        findings += _optionals(source, cls)
        findings += _constructor_raises(source, cls)
    return sorted(findings, key=lambda finding: (finding.line, finding.col, finding.code))


def _fields(cls: ast.ClassDef) -> list[tuple[ast.AnnAssign, str, ast.expr]]:
    """Les champs annotés de la classe : l'instruction, le nom et l'annotation, `Mapped[X]` lu comme `X`."""
    return [
        (stmt, stmt.target.id, _unwrap_mapped(stmt.annotation))
        for stmt in cls.body
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
    ]


def _unwrap_mapped(annotation: ast.expr) -> ast.expr:
    if isinstance(annotation, ast.Subscript) and _name_of(annotation.value) == "Mapped":
        return annotation.slice
    return annotation


def _name_of(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _union_members(annotation: ast.expr) -> list[ast.expr]:
    """Les membres d'une union `A | B | None`, `Optional[A]` ou `Union[A, B]`, ou l'annotation seule."""
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return [*_union_members(annotation.left), *_union_members(annotation.right)]
    if isinstance(annotation, ast.Subscript) and _name_of(annotation.value) == "Optional":
        return [*_union_members(annotation.slice), ast.Constant(value=None)]
    if isinstance(annotation, ast.Subscript) and _name_of(annotation.value) == "Union":
        members = (
            annotation.slice.elts if isinstance(annotation.slice, ast.Tuple) else [annotation.slice]
        )
        return [member for part in members for member in _union_members(part)]
    return [annotation]


def _is_none(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _is_optional(annotation: ast.expr) -> bool:
    return any(_is_none(member) for member in _union_members(annotation))


def _is_bool(annotation: ast.expr) -> bool:
    return any(_name_of(member) == "bool" for member in _union_members(annotation))


def _flags(source: Source, cls: ast.ClassDef) -> list[Finding]:
    return [
        Finding(
            path=source.path,
            line=stmt.lineno,
            col=stmt.col_offset + 1,
            code=CODE_FLAG,
            message=(
                f"champ booléen stocké `{name}` dans `{cls.name}` : "
                "une variante d'union fermée par valeur du drapeau"
            ),
        )
        for stmt, name, annotation in _fields(cls)
        if name.startswith(FLAG_PREFIXES) and _is_bool(annotation)
    ]


def _optionals(source: Source, cls: ast.ClassDef) -> list[Finding]:
    optional = [(stmt, name) for stmt, name, annotation in _fields(cls) if _is_optional(annotation)]
    if len(optional) < 2:
        return []
    names = ", ".join(f"`{name}`" for _, name in optional)
    return [
        Finding(
            path=source.path,
            line=cls.lineno,
            col=cls.col_offset + 1,
            code=CODE_OPTIONALS,
            message=(
                f"`{cls.name}` a {len(optional)} champs `| None` ({names}) : "
                "une variante par combinaison légale, sans `None`"
            ),
        )
    ]


def _constructor_raises(source: Source, cls: ast.ClassDef) -> list[Finding]:
    return [
        Finding(
            path=source.path,
            line=node.lineno,
            col=node.col_offset + 1,
            code=CODE_CONSTRUCTOR,
            message=(
                f"`raise` dans `{method.name}` de `{cls.name}` : "
                "valider dans une fabrique qui rend un résultat"
            ),
        )
        for method in cls.body
        if isinstance(method, ast.FunctionDef) and method.name in CONSTRUCTORS
        for node in ast.walk(method)
        if isinstance(node, ast.Raise)
    ]
