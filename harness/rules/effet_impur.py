"""Règle 6 : le modèle appelle-t-il des effets impurs (heure, aléatoire, UUID, fichier, réseau, environnement) ?

Toute référence à un effet impur dans le modèle (`domain/model`, et `anemic_model` tant que la règle 3 n'est pas
faite) est un constat (EI001). Le cœur reçoit l'effet en paramètre, ou par un port écrit dans le langage du métier
(`Clock`, `IdGenerator`) que l'on injecte : ses tests se font alors avec de simples faux, sans `patch`.

La règle lit les références, appelées ou non. `field(default_factory=uuid4)` n'appelle rien dans le modèle, et laisse
pourtant l'effet y entrer. Les noms sont résolus par les imports du fichier : `import datetime as dt` puis
`dt.datetime.now()`, ou `from datetime import date as d` puis `d.today`, sont vus comme `datetime.datetime.now` et
`datetime.date.today`. Importer `date` pour typer un champ reste permis : l'effet est `date.today`.

Les tests du cœur sont lus aussi (EI002) : un `patch`, un `monkeypatch`, un `mocker.patch` ou un `freezegun` y remplace
l'effet au lieu de le recevoir. Le cœur pur reçoit un faux en paramètre, le test n'a plus rien à remplacer.

Une règle travaille fichier par fichier, donc une fonction du modèle qui appelle un autre module pur qui appelle
l'horloge échappe à la règle. Elle offre un premier pas, sans garantie.

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`.
"""

import ast
from dataclasses import dataclass

from harness.rules.sources import Source, dotted, import_aliases, qualify
from harness.rules.ubiquitous_language import UbiquitousLanguage

CODE = "EI001"
CODE_TESTS = "EI002"

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
# Ce qui remplace un effet dans un test : `unittest.mock.patch` (et `.object`, `.dict`), `freezegun`, `time_machine`.
PATCH_NAMES = frozenset({"unittest.mock.patch"})
PATCH_MODULES = frozenset({"freezegun", "time_machine"})
# Les fixtures pytest qui remplacent : `monkeypatch.setattr(...)`, `mocker.patch(...)`.
PATCH_FIXTURES = {"monkeypatch": None, "mocker": "patch"}


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


def check_tests(source: Source, language: UbiquitousLanguage) -> list[Finding]:
    """Un constat par remplacement d'effet dans un fichier de test, dans l'ordre des lignes."""
    visitor = _Patches(source)
    visitor.visit(source.tree)
    return sorted(visitor.findings, key=lambda finding: (finding.line, finding.col))


def _is_patch(qualified: str) -> bool:
    return any(
        qualified == name or qualified.startswith(f"{name}.")
        for name in PATCH_NAMES | PATCH_MODULES
    )


def _is_impure(qualified: str) -> bool:
    return qualified in IMPURE_NAMES or any(
        qualified == module or qualified.startswith(f"{module}.") for module in IMPURE_MODULES
    )


class _Walker(ast.NodeVisitor):
    """Ce que les deux lectures partagent : les alias d'import et la construction d'un constat."""

    code = CODE
    advice = ""

    def __init__(self, source: Source) -> None:
        self._path = source.path
        self.findings: list[Finding] = []
        self._aliases = import_aliases(source.tree)

    def _qualify(self, parts: list[str]) -> str:
        return qualify(parts, self._aliases)

    def _report(self, node: ast.expr, effect: str) -> None:
        self.findings.append(
            Finding(
                path=self._path,
                line=node.lineno,
                col=node.col_offset + 1,
                effect=effect,
                code=self.code,
                message=f"`{effect}` {self.advice}",
            )
        )


class _Effects(_Walker):
    advice = (
        "dans le modèle : l'effet entre par un paramètre ou par un port du métier "
        "(`Clock`, `IdGenerator`)"
    )

    def __init__(self, source: Source) -> None:
        super().__init__(source)
        self._defined = _defined_names(source.tree)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        parts = dotted(node)
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


class _Patches(_Walker):
    code = CODE_TESTS
    advice = (
        "dans un test : le cœur reçoit un faux en paramètre, le test n'a plus d'effet à remplacer"
    )

    def visit_Attribute(self, node: ast.Attribute) -> None:
        parts = dotted(node)
        if parts is not None and (self._is_fixture_patch(parts) or _is_patch(self._qualify(parts))):
            self._report(node, ".".join(parts))
            return
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            qualified = self._qualify([node.id])
            if qualified != node.id and _is_patch(qualified):
                self._report(node, node.id)

    @staticmethod
    def _is_fixture_patch(parts: list[str]) -> bool:
        if parts[0] not in PATCH_FIXTURES or len(parts) < 2:
            return False
        method = PATCH_FIXTURES[parts[0]]
        return method is None or parts[1] == method


def _defined_names(tree: ast.Module) -> set[str]:
    """Les fonctions, classes et paramètres que le fichier définit : ils masquent les fonctions natives."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names
