"""Règle 10 : le cœur ne dépend-il que de lui-même ?

Tout `import` du cœur (`domain`, et `anemic_model` tant que la règle 3 n'est pas faite) vers autre chose que le cœur,
le noyau (`kernel`) et les ports (`ports`), la bibliothèque `result` ou les outils de programmation de la bibliothèque standard (`STDLIB_ALLOWED` :
`dataclasses`, `typing`, `enum`, `decimal`…) est un constat (AO001). SQLAlchemy, FastAPI, `requests`, mais aussi
`controller`, `service`, `dal`, `infrastructure`, `config`, `database`, et les modules de la bibliothèque standard qui
touchent le monde (`os`, `sys`, `time`, `random`, `json`, `pathlib`, `logging`…) restent à l'extérieur. Le cœur décrit
ce dont il a besoin par un port (`Protocol`) que l'extérieur implémente.

La règle lit les imports, y compris ceux d'un bloc `if TYPE_CHECKING:` : une annotation est déjà une dépendance.
Les imports relatifs sont résolus contre le nom du module. La règle 6 reste utile : `datetime` et `uuid` sont permis
pour typer, mais `date.today()` et `uuid4()` y sont des constats.

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`.
"""

import ast
from dataclasses import dataclass

from harness.perimetre import PACKAGE
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage

CODE = "AO001"

KERNEL = f"{PACKAGE}.kernel"
PORTS = f"{PACKAGE}.ports"
DOMAIN = f"{PACKAGE}.domain"
ANEMIC = f"{PACKAGE}.anemic_model"
# Les anneaux de l'oignon, et ce que chacun peut importer de ce projet. Le noyau (`kernel`) est l'anneau le plus
# intérieur : il n'importe que lui-même. Les ports (`ports`) ne décrivent que des `Protocol` et n'importent que le
# noyau. Le cœur (`domain`, et `anemic_model` tant que la règle 3 n'a pas rangé le modèle) peut importer le noyau et
# les ports, mais rien de plus extérieur. Un module hors de ces anneaux n'est pas inspecté.
PEUT_IMPORTER = {
    KERNEL: (KERNEL,),
    PORTS: (KERNEL, PORTS),
    DOMAIN: (DOMAIN, ANEMIC, KERNEL, PORTS),
    ANEMIC: (DOMAIN, ANEMIC, KERNEL, PORTS),
}
# Les seules bibliothèques extérieures permises : celle des résultats `Ok` / `Err` (règle 5).
ALLOWED_LIBRARIES = frozenset({"result"})
# La bibliothèque standard permise : des outils de programmation purs, sans accès au système, au disque ni au réseau.
STDLIB_ALLOWED = frozenset(
    {
        "__future__",
        "abc",
        "collections",
        "contextlib",
        "copy",
        "dataclasses",
        "datetime",
        "decimal",
        "enum",
        "fractions",
        "functools",
        "itertools",
        "math",
        "numbers",
        "operator",
        "re",
        "statistics",
        "string",
        "textwrap",
        "types",
        "typing",
        "uuid",
    }
)


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
    """Un constat par import qui sort de l'anneau du module, dans l'ordre des lignes."""
    anneau = _anneau(source.module)
    if anneau is None:
        return []
    findings = [
        _finding(source, node, target)
        for node in ast.walk(source.tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for target in _targets(source, node)
        if not _is_allowed(target, anneau)
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


def _anneau(module: str) -> str | None:
    """L'anneau auquel appartient le module, ou `None` s'il n'est pas inspecté."""
    for anneau in PEUT_IMPORTER:
        if module == anneau or module.startswith(f"{anneau}."):
            return anneau
    return None


def _is_allowed(target: str, anneau: str) -> bool:
    root = target.split(".")[0]
    if root == PACKAGE:
        return any(
            target == permis or target.startswith(f"{permis}.") for permis in PEUT_IMPORTER[anneau]
        )
    return root in STDLIB_ALLOWED or root in ALLOWED_LIBRARIES
