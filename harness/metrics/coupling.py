"""Couplage d'une classe : fan-out et CBO.

Fan-out : le nombre de types (classes) dont la classe dépend, en regardant ce qu'elle importe ou définit à côté d'elle.
CBO (Coupling Between Objects) : le fan-out plus le fan-in, c'est-à-dire tous les types couplés à la classe, dans un sens
ou dans l'autre. Une classe peut avoir peu de dépendances et être utilisée partout : le CBO la montre, pas le fan-out.

Limites assumées : on lit les noms, on ne résout pas les types (pas d'inférence). Un type n'est compté que si son nom
est en CapWords (la convention PEP 8) : les fonctions et les constantes importées ne comptent pas. La bibliothèque
standard est exclue (comme java.lang pour PMD). Les annotations écrites en chaîne ("Product") ne sont pas lues.
"""

import ast
import sys
from collections.abc import Mapping
from dataclasses import dataclass

from harness.metrics.classes import top_level_classes
from harness.metrics.sources import SourceFile

type ImportTable = dict[str, str]

_MAX_REEXPORT_DEPTH = 5


@dataclass(frozen=True)
class Coupling:
    fan_out: int
    cbo: int
    dependencies: frozenset[str]


def measure(sources: list[SourceFile]) -> dict[str, Coupling]:
    """Le couplage de chaque classe de premier niveau, par nom qualifié (`omni_product.model.product.Product`)."""
    tables = {source.module: _import_table(source) for source in sources}
    outgoing = {
        f"{source.module}.{cls.name}": _resolve_all(
            _dependencies(source, cls, tables[source.module]), tables
        )
        - {f"{source.module}.{cls.name}"}
        for source in sources
        for cls in top_level_classes(source.tree)
    }
    return {
        name: Coupling(
            fan_out=len(out),
            cbo=len(out | {other for other, targets in outgoing.items() if name in targets}),
            dependencies=frozenset(out),
        )
        for name, out in outgoing.items()
    }


def _import_table(source: SourceFile) -> ImportTable:
    """Nom lié dans le module, vers le nom qualifié de ce qu'il désigne."""
    table: ImportTable = {}
    for node in ast.walk(source.tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                table[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom):
            base = _absolute_module(source, node)
            for alias in node.names:
                if alias.name != "*":
                    table[alias.asname or alias.name] = f"{base}.{alias.name}"
    return table


def _absolute_module(source: SourceFile, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    package = source.module.split(".")
    if not source.is_package:
        package = package[:-1]
    package = package[: len(package) - (node.level - 1)]
    return ".".join([*package, *(node.module.split(".") if node.module else [])])


def _is_type_name(name: str) -> bool:
    """CapWords : une majuscule en tête, et pas une CONSTANTE."""
    return name[:1].isupper() and not name.isupper()


def _is_stdlib(qualified: str) -> bool:
    return qualified.split(".")[0] in sys.stdlib_module_names


def _dependencies(source: SourceFile, cls: ast.ClassDef, table: ImportTable) -> set[str]:
    local_classes = {c.name for c in top_level_classes(source.tree)} - {cls.name}
    found: set[str] = set()
    for node in ast.walk(cls):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in table:
                found.add(table[node.id])
            elif node.id in local_classes:
                found.add(f"{source.module}.{node.id}")
        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in table
        ):
            found.add(f"{table[node.value.id]}.{node.attr}")
    return {
        name for name in found if _is_type_name(name.rsplit(".", 1)[-1]) and not _is_stdlib(name)
    }


def _resolve_all(names: set[str], tables: Mapping[str, ImportTable]) -> set[str]:
    return {_resolve(name, tables) for name in names}


def _resolve(name: str, tables: Mapping[str, ImportTable], depth: int = 0) -> str:
    """Suit les ré-exports : `omni_product.model.Product` (via `model/__init__.py`) devient `...model.product.Product`."""
    module, _, member = name.rpartition(".")
    target = tables.get(module, {}).get(member)
    if target is None or target == name or depth >= _MAX_REEXPORT_DEPTH:
        return name
    return _resolve(target, tables, depth + 1)
