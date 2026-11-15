"""Règle 2 : chaque classe du modèle est-elle une entité ou un Value Object ?

Une entité porte un champ `id` d'un type dédié (`ProductId`, pas `str`). Un Value Object est une `dataclass(frozen=True)`
sans identifiant. Chaque classe du modèle est l'une des deux, et rien d'autre. Les Enum, Protocol, TypedDict et
exceptions sont exceptés, comme dans la règle 4.

Un membre de l'ubiquitous language (`price`, `slug`) déclaré en type primitif brut (`float`, `str`) est une primitive du domaine
qui devrait être un Value Object.

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`.
"""

import ast
from dataclasses import dataclass

from harness.rules.sources import Source, public_members, top_level_classes
from harness.rules.language import UbiquitousLanguage

# Une classe qui n'est ni entité ni Value Object.
KIND_CODE = "EV001"
# Un membre de l'ubiquitous language en type primitif brut.
PRIMITIVE_CODE = "EV002"

PRIMITIVES = frozenset({"str", "int", "float", "bool", "bytes", "Decimal"})
# Enveloppes qui ne changent pas le type porté : `Mapped[str]` est un `str`.
_WRAPPERS = frozenset({"Mapped", "Optional", "ClassVar"})
_EXEMPT_BASES = frozenset({"Enum", "StrEnum", "IntEnum", "Protocol", "TypedDict"})


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
    findings: list[Finding] = []
    classes = {cls.name: cls for cls in top_level_classes(source.tree)}
    for cls in classes.values():
        if _is_exempt(cls):
            continue
        findings.extend(_kind_findings(cls, classes, source.path))
        findings.extend(_primitive_findings(cls, source.path, language))
    return findings


def _kind_findings(cls: ast.ClassDef, classes: dict[str, ast.ClassDef], path: str) -> list[Finding]:
    identifier = _identifier_of(cls, classes)
    if identifier is not None:
        if _is_primitive(identifier.annotation):
            annotation = ast.unparse(identifier.annotation)
            return [
                _finding(
                    path,
                    cls,
                    KIND_CODE,
                    f"'{cls.name}' a un identifiant de type primitif ({annotation}) : "
                    "une entité porte un type dédié, comme ProductId",
                )
            ]
        return []
    if _is_frozen_dataclass(cls):
        return []
    return [
        _finding(
            path,
            cls,
            KIND_CODE,
            f"'{cls.name}' n'est ni une entité (id typé) ni un Value Object "
            "(dataclass frozen sans id)",
        )
    ]


def _primitive_findings(cls: ast.ClassDef, path: str, language: UbiquitousLanguage) -> list[Finding]:
    findings: list[Finding] = []
    for name, line, node in public_members(cls):
        if not isinstance(node, ast.AnnAssign) or name.startswith("_"):
            continue
        if language.is_link(name) or not _is_primitive(node.annotation):
            continue
        concern = language.concern_of(name)
        if concern is None:
            continue
        annotation = ast.unparse(node.annotation)
        findings.append(
            Finding(
                path=path,
                line=line,
                col=node.col_offset + 1,
                cls=cls.name,
                code=PRIMITIVE_CODE,
                message=(
                    f"'{cls.name}' porte '{name}' ({concern}) en type primitif ({annotation}) : "
                    "un Value Object est attendu"
                ),
            )
        )
    return findings


def _identifier_of(cls: ast.ClassDef, classes: dict[str, ast.ClassDef]) -> ast.AnnAssign | None:
    """Le champ `id` annoté de la classe, ou celui de la plus proche classe parente du même module."""
    seen: set[str] = set()
    pending = [cls]
    while pending:
        current = pending.pop(0)
        if current.name in seen:
            continue
        seen.add(current.name)
        for stmt in current.body:
            if (
                isinstance(stmt, ast.AnnAssign)
                and isinstance(stmt.target, ast.Name)
                and stmt.target.id == "id"
            ):
                return stmt
        pending.extend(classes[base] for base in _base_names(current) if base in classes)
    return None


def _base_names(cls: ast.ClassDef) -> list[str]:
    names: list[str] = []
    for base in cls.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            names.append(base.attr)
    return names


def _is_exempt(cls: ast.ClassDef) -> bool:
    return any(
        name in _EXEMPT_BASES or name.endswith(("Error", "Exception")) for name in _base_names(cls)
    )


def _is_frozen_dataclass(cls: ast.ClassDef) -> bool:
    for decorator in cls.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        func = decorator.func
        called = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
        if called != "dataclass":
            continue
        for keyword in decorator.keywords:
            if (
                keyword.arg == "frozen"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
            ):
                return True
    return False


def _is_primitive(annotation: ast.expr) -> bool:
    """Vrai si l'annotation ne nomme que des types primitifs (`str`, `float | None`, `Mapped[int]`…)."""
    names: set[str] = set()
    for node in ast.walk(annotation):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    names -= _WRAPPERS
    return bool(names) and names <= PRIMITIVES


def _finding(path: str, cls: ast.ClassDef, code: str, message: str) -> Finding:
    return Finding(path, cls.lineno, cls.col_offset + 1, cls.name, code, message)
