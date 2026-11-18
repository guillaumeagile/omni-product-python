"""Règle 6 : le modèle appelle-t-il des effets impurs (heure, aléatoire, UUID, fichier, réseau, environnement) ?

Toute référence à un effet impur dans le modèle (`domain/model`, et `anemic_model` tant que la règle 3 n'est pas
faite) est un constat (EI001). Le cœur reçoit l'effet en paramètre, ou par un port écrit dans le langage du métier
(`Clock`, `IdGenerator`) que l'on injecte : ses tests se font alors avec de simples faux, sans `patch`.

La règle lit les références, appelées ou non. `field(default_factory=uuid4)` n'appelle rien dans le modèle, et laisse
pourtant l'effet y entrer. Les noms sont résolus par les imports du fichier : `import datetime as dt` puis
`dt.datetime.now()`, ou `from datetime import date as d` puis `d.today`, sont vus comme `datetime.datetime.now` et
`datetime.date.today`. Importer `date` pour typer un champ reste permis : l'effet est `date.today`.

Une règle travaille fichier par fichier, donc une fonction du modèle qui appelle un autre module pur qui appelle
l'horloge échappe à la règle. Elle offre un premier pas, sans garantie.

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`.
"""

import ast
from dataclasses import dataclass

from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage

CODE = "EI001"

# Les fonctions et attributs impurs, par nom qualifié.
IMPURE_NAMES = frozenset(
    {
        "datetime.date.today",
        "datetime.datetime.now",
        "datetime.datetime.today",
        "datetime.datetime.utcnow",
        "time.time",
        "time.time_ns",
        "time.monotonic",
        "time.perf_counter",
        "time.sleep",
        "uuid.uuid1",
        "uuid.uuid4",
        "os.getenv",
        "os.getcwd",
    }
)
# Les modules dont tout ce qu'on atteint est un effet.
IMPURE_MODULES = frozenset(
    {
        "random",
        "secrets",
        "os.environ",
        "logging",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "shutil",
        "urllib.request",
    }
)
# Les fonctions natives impures : lues seulement quand elles sont appelées et que le fichier ne les redéfinit pas.
IMPURE_BUILTINS = frozenset({"open", "print", "input"})


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    col: int
    effect: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}:{self.col}: {self.code} {self.message}"


def check(source: Source, language: UbiquitousLanguage) -> list[Finding]:
    """Un constat par référence à un effet impur, dans l'ordre des lignes."""
    visitor = _Effects(source)
    visitor.visit(source.tree)
    return sorted(visitor.findings, key=lambda finding: (finding.line, finding.col))


def _is_impure(qualified: str) -> bool:
    return qualified in IMPURE_NAMES or any(
        qualified == module or qualified.startswith(f"{module}.") for module in IMPURE_MODULES
    )


class _Effects(ast.NodeVisitor):
    def __init__(self, source: Source) -> None:
        self._path = source.path
        self.findings: list[Finding] = []
        self._aliases = _aliases(source.tree)
        self._defined = _defined_names(source.tree)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        parts = _dotted(node)
        if parts is not None:
            qualified = self._qualify(parts)
            if _is_impure(qualified):
                self._report(node, qualified)
                return
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            qualified = self._qualify([node.id])
            if qualified != node.id and _is_impure(qualified):
                self._report(node, qualified)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if (
            isinstance(func, ast.Name)
            and func.id in IMPURE_BUILTINS
            and func.id not in self._aliases
            and func.id not in self._defined
        ):
            self._report(func, func.id)
        else:
            self.visit(func)
        for child in (*node.args, *node.keywords):
            self.visit(child)

    def _qualify(self, parts: list[str]) -> str:
        root = self._aliases.get(parts[0], parts[0])
        return ".".join([root, *parts[1:]])

    def _report(self, node: ast.expr, effect: str) -> None:
        self.findings.append(
            Finding(
                path=self._path,
                line=node.lineno,
                col=node.col_offset + 1,
                effect=effect,
                code=CODE,
                message=(
                    f"`{effect}` dans le modèle : l'effet entre par un paramètre "
                    "ou par un port du métier (`Clock`, `IdGenerator`)"
                ),
            )
        )


def _dotted(node: ast.expr) -> list[str] | None:
    """`a.b.c` en `["a", "b", "c"]`, ou `None` quand la chaîne ne part pas d'un nom (`f().b`)."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    return [node.id, *reversed(parts)]


def _aliases(tree: ast.Module) -> dict[str, str]:
    """Le nom local de chaque import, vers le nom qualifié : `d` vaut `datetime.date` après `from datetime import date as d`."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    aliases[alias.asname] = alias.name
                else:
                    root = alias.name.split(".")[0]
                    aliases[root] = root
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return aliases


def _defined_names(tree: ast.Module) -> set[str]:
    """Les fonctions, classes et paramètres que le fichier définit : ils masquent les fonctions natives."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names
