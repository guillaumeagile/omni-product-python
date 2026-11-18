"""Règle 10 : le cœur ne dépend-il que de lui-même ?

Tout `import` du cœur (`domain`, et `anemic_model` tant que la règle 3 n'est pas faite) vers autre chose que le cœur
lui-même, la bibliothèque standard ou la bibliothèque `result` est un constat (AO001). SQLAlchemy, FastAPI, `requests`,
mais aussi `controller`, `service`, `dal`, `infrastructure`, `config` et `database` restent à l'extérieur. Le cœur
décrit ce dont il a besoin par un port (`Protocol`) que l'extérieur implémente.

La règle lit les imports, y compris ceux d'un bloc `if TYPE_CHECKING:` : une annotation est déjà une dépendance.
Les imports relatifs sont résolus contre le nom du module. Les effets de la bibliothèque standard (heure, fichier,
réseau) restent l'affaire de la règle 6.

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`.
"""

import ast
import sys
from dataclasses import dataclass

from harness.perimetre import PACKAGE
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage

CODE = "AO001"

# Ce que le cœur peut importer de ce projet : lui-même. `anemic_model` y est tant que la règle 3 n'a pas rangé le modèle.
CORE = (f"{PACKAGE}.domain", f"{PACKAGE}.anemic_model")
# Les seules bibliothèques extérieures permises : celle des résultats `Ok` / `Err` (règle 5).
ALLOWED_LIBRARIES = frozenset({"result"})


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    col: int
    target: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}:{self.col}: {self.code} {self.message}"


def check(source: Source, language: UbiquitousLanguage) -> list[Finding]:
    """Un constat par import qui sort du cœur, dans l'ordre des lignes."""
    findings = [
        _finding(source, node, target)
        for node in ast.walk(source.tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for target in _targets(source, node)
        if not _is_allowed(target)
    ]
    return sorted(findings, key=lambda finding: (finding.line, finding.col))


def _finding(source: Source, node: ast.stmt, target: str) -> Finding:
    return Finding(
        path=source.path,
        line=node.lineno,
        col=node.col_offset + 1,
        target=target,
        code=CODE,
        message=f"`{target}` dans le cœur : il dépend d'un port, l'extérieur l'implémente",
    )


def _targets(source: Source, node: ast.Import | ast.ImportFrom) -> list[str]:
    """Les modules importés par l'instruction, en nom absolu."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    module = _absolute(source, node)
    if node.level == 0 or not node.module:
        # `from . import x` importe un module frère : le nom importé fait partie de la cible.
        return [module] if node.module else [f"{module}.{alias.name}" for alias in node.names]
    return [module]


def _absolute(source: Source, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    parts = source.module.split(".")
    if not source.path.endswith("__init__.py"):
        parts = parts[:-1]
    parts = parts[: len(parts) - (node.level - 1)]
    return ".".join([*parts, *([node.module] if node.module else [])])


def _is_allowed(target: str) -> bool:
    root = target.split(".")[0]
    if root == PACKAGE:
        return any(target == core or target.startswith(f"{core}.") for core in CORE)
    return root in sys.stdlib_module_names or root in ALLOWED_LIBRARIES
