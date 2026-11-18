"""Règle 10 : le cœur ne dépend-il que de lui-même ?

La règle ne connaît aucun nom de répertoire. Elle reconnaît le cœur à ce qu'il contient et à sa place dans le graphe
des imports, pour qu'une équipe puisse ranger ou renommer ses paquets (`kernel`, `ports`, `adapters`…) sans la tromper.

1. Une **ancre** est un module qui déclare un concept du métier : une classe dont le nom contient un mot de
   l'ubiquitous language, et qui n'hérite pas directement d'une classe d'une bibliothèque extérieure (un `BaseModel`
   pydantic ou un `DeclarativeBase` SQLAlchemy sont des formats d'échange). Le reste du projet doit en dépendre : des
   modules d'au moins deux autres sous-paquets l'importent.
2. Le **cœur** contient les modules du paquet d'une ancre, et tout ce qu'ils importent du projet, de proche en proche.
3. Dans le cœur, un import vers autre chose que le projet, la bibliothèque `result` ou les outils de programmation de
   la bibliothèque standard (`STDLIB_ALLOWED` : `dataclasses`, `typing`, `enum`, `decimal`…) est un constat (AO001).
   SQLAlchemy, FastAPI, `requests`, et les modules de la bibliothèque standard qui touchent le monde (`os`, `sys`,
   `time`, `random`, `json`, `pathlib`, `logging`…) restent à l'extérieur. Un import vers un module du projet
   introuvable est aussi un constat : la règle ne peut pas le juger, elle le refuse.
4. Un import du cœur vers un module du projet qui dépend en retour de celui qui l'importe forme un cycle (AO002) : un
   service ou un adaptateur importé par le cœur, par exemple.

Le cœur décrit ce dont il a besoin par un port (`Protocol`) que l'extérieur implémente.

La règle lit les imports, y compris ceux d'un bloc `if TYPE_CHECKING:` : une annotation est déjà une dépendance.
Les imports relatifs sont résolus contre le nom du module. La règle 6 reste utile : `datetime` et `uuid` sont permis
pour typer, mais `date.today()` et `uuid4()` y sont des constats.

Limite connue : un module pur de l'extérieur (un service sans effet), importé par le cœur sans cycle, n'est pas un
constat. La règle juge la pureté et le sens des dépendances, elle ne devine pas l'intention.

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`.
"""

import ast
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from harness.perimetre import PACKAGE
from harness.rules.sources import Source, top_level_classes
from harness.rules.ubiquitous_language import UbiquitousLanguage, words

CODE = "AO001"
CYCLE_CODE = "AO002"

# Une ancre est importée par des modules d'au moins ce nombre d'autres sous-paquets.
ANCRE_SOUS_PAQUETS = 2
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


@dataclass(frozen=True)
class Import:
    node: ast.stmt
    # Le module importé, en nom absolu.
    target: str
    # Les modules du projet que l'instruction charge : le module importé, et un sous-module nommé par `from x import y`.
    modules: tuple[str, ...]


def check(source: Source, language: UbiquitousLanguage) -> list[Finding]:
    """Le fichier seul, lu comme un module du cœur : un constat par import qui sort du projet sans être permis.

    Sans le reste du paquet, la règle ne juge pas les imports du projet. `check_paquet` les juge.
    """
    return sorted(
        (
            _finding(source, imp.node, imp.target)
            for imp in _imports(source, frozenset())
            if not _is_project(imp.target) and not _is_allowed_library(imp.target)
        ),
        key=_order,
    )


def check_paquet(sources: Sequence[Source], language: UbiquitousLanguage) -> list[Finding]:
    """Un constat par import du cœur qui sort de l'oignon, fichier par fichier, dans l'ordre des lignes."""
    by_module = {source.module: source for source in sources}
    known = frozenset(by_module)
    imports = {module: _imports(source, known) for module, source in by_module.items()}
    edges = {
        module: frozenset(m for imp in found for m in imp.modules if m in known)
        for module, found in imports.items()
    }
    impure = _impure(imports, known, edges)
    findings: list[Finding] = []
    for module in sorted(_core(by_module, edges, language)):
        source = by_module[module]
        own = frozenset(m for m, s in by_module.items() if _package(s) == _package(source))
        findings.extend(
            sorted(_core_findings(source, imports[module], own, impure, edges), key=_order)
        )
    return findings


def _core_findings(
    source: Source,
    imports: Iterable[Import],
    own: frozenset[str],
    impure: frozenset[str],
    edges: dict[str, frozenset[str]],
) -> list[Finding]:
    """Les imports d'un module du cœur qui sortent de l'oignon.

    Un import du même paquet est jugé là où il est déclaré. Un import d'un autre paquet du projet est un cycle s'il
    revient vers ce paquet (AO002), et une sortie s'il atteint une bibliothèque interdite, même de loin (AO001).
    """
    findings: list[Finding] = []
    for imp in imports:
        if not _is_project(imp.target):
            if not _is_allowed_library(imp.target):
                findings.append(_finding(source, imp.node, imp.target))
            continue
        resolved = [m for m in imp.modules if m in edges]
        if not resolved:
            findings.append(_finding(source, imp.node, imp.target))
            continue
        others = [m for m in resolved if m not in own]
        if any(own & (_reachable(m, edges) | {m}) for m in others):
            findings.append(_cycle_finding(source, imp.node, imp.target))
        elif any(m in impure for m in others):
            findings.append(_finding(source, imp.node, imp.target))
    return findings


def _impure(
    imports: dict[str, list[Import]],
    known: frozenset[str],
    edges: dict[str, frozenset[str]],
) -> frozenset[str]:
    """Les modules qui atteignent une bibliothèque interdite ou un module introuvable, eux-mêmes ou de proche en proche."""
    direct = {
        module
        for module, found in imports.items()
        if any(
            (not _is_project(imp.target) and not _is_allowed_library(imp.target))
            or (_is_project(imp.target) and not any(m in known for m in imp.modules))
            for imp in found
        )
    }
    return frozenset(m for m in edges if m in direct or direct & _reachable(m, edges))


def _core(
    by_module: dict[str, Source],
    edges: dict[str, frozenset[str]],
    language: UbiquitousLanguage,
) -> frozenset[str]:
    """Les modules des paquets d'ancrage : un paquet qui déclare un concept du métier, et dont le reste dépend.

    Le reste dépend d'un paquet quand des modules d'au moins `ANCRE_SOUS_PAQUETS` autres sous-paquets importent un de
    ses modules (son `__init__.py` compris : on importe souvent le paquet plutôt que le module).
    """
    package_of = {module: _package(source) for module, source in by_module.items()}
    importers: dict[str, set[str]] = {package: set() for package in package_of.values()}
    for module, targets in edges.items():
        for target in targets:
            importers[package_of[target]].add(_top(module))
    concepts = _concept_words(language)
    vocabulary = concepts | language.generic_words
    packages = {
        package_of[module]
        for module, source in by_module.items()
        if _declares_concept(source, concepts, vocabulary)
        and len(importers[package_of[module]] - {_top(module)}) >= ANCRE_SOUS_PAQUETS
    }
    return frozenset(module for module, package in package_of.items() if package in packages)


def _reachable(start: str, edges: dict[str, frozenset[str]]) -> frozenset[str]:
    """Les modules que `start` importe, directement ou de proche en proche."""
    seen: set[str] = set()
    pending = list(edges.get(start, ()))
    while pending:
        module = pending.pop()
        if module not in seen:
            seen.add(module)
            pending.extend(edges.get(module, ()))
    return frozenset(seen)


def _concept_words(language: UbiquitousLanguage) -> frozenset[str]:
    return frozenset(word for keyword in language.keywords for word in keyword.words)


def _declares_concept(source: Source, concepts: frozenset[str], vocabulary: frozenset[str]) -> bool:
    """Le module déclare une classe du métier, sans base prise à une bibliothèque extérieure.

    Son nom n'a que des mots de l'ubiquitous language (et des mots génériques comme `id`), dont un concept au moins :
    `Product`, `ProductId`, `RegionSupplier`. `ProductService`, `ProductSchema` ou `ImpactCo2Request` n'en sont pas.
    """
    external = _external_names(source)
    return any(
        set(words(cls.name)) <= vocabulary
        and bool(concepts.intersection(words(cls.name)))
        and not any(_base_name(base) in external for base in cls.bases)
        for cls in top_level_classes(source.tree)
    )


def _external_names(source: Source) -> frozenset[str]:
    """Les noms locaux importés d'une bibliothèque extérieure au projet et à la bibliothèque standard permise."""
    names: set[str] = set()
    for node in ast.walk(source.tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if not _is_project(node.module) and not _is_allowed_library(node.module):
                names.update(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if not _is_project(alias.name) and not _is_allowed_library(alias.name):
                    names.add(alias.asname or alias.name.split(".")[0])
    return frozenset(names)


def _base_name(base: ast.expr) -> str:
    """Le premier nom d'une base : `Base` pour `Base`, `orm` pour `orm.DeclarativeBase`."""
    while isinstance(base, ast.Attribute):
        base = base.value
    if isinstance(base, ast.Subscript):
        return _base_name(base.value)
    return base.id if isinstance(base, ast.Name) else ""


def _top(module: str) -> str:
    """Le sous-paquet de premier niveau : `domain` pour `omni_product.domain.model.product`."""
    parts = module.split(".")
    return parts[1] if len(parts) > 1 else parts[0]


def _package(source: Source) -> str:
    """Le paquet qui contient le module : lui-même pour un `__init__.py`."""
    if source.path.endswith("__init__.py"):
        return source.module
    return source.module.rpartition(".")[0]


def _finding(source: Source, node: ast.stmt, target: str) -> Finding:
    return Finding(
        path=source.path,
        line=node.lineno,
        col=node.col_offset + 1,
        target=target,
        code=CODE,
        message=f"`{target}` dans le cœur : il dépend d'un port, l'extérieur l'implémente",
    )


def _cycle_finding(source: Source, node: ast.stmt, target: str) -> Finding:
    return Finding(
        path=source.path,
        line=node.lineno,
        col=node.col_offset + 1,
        target=target,
        code=CYCLE_CODE,
        message=f"`{target}` dépend du cœur qui l'importe : le cycle sort de l'oignon",
    )


def _order(finding: Finding) -> tuple[int, int]:
    return (finding.line, finding.col)


def _imports(source: Source, known: frozenset[str]) -> list[Import]:
    """Chaque module importé par le fichier, avec les modules du projet que l'instruction charge."""
    found: list[Import] = []
    for node in ast.walk(source.tree):
        if isinstance(node, ast.Import):
            found.extend(Import(node, alias.name, (alias.name,)) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.extend(_from_imports(source, node, known))
    return found


def _from_imports(source: Source, node: ast.ImportFrom, known: frozenset[str]) -> list[Import]:
    module = _absolute(source, node)
    if not node.module:
        # `from . import x` importe un module frère : le nom importé fait partie de la cible.
        return [
            Import(node, f"{module}.{alias.name}", (f"{module}.{alias.name}",))
            for alias in node.names
        ]
    submodules = tuple(
        f"{module}.{alias.name}" for alias in node.names if f"{module}.{alias.name}" in known
    )
    return [Import(node, module, (module, *submodules))]


def _absolute(source: Source, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    parts = source.module.split(".")
    if not source.path.endswith("__init__.py"):
        parts = parts[:-1]
    parts = parts[: len(parts) - (node.level - 1)]
    return ".".join([*parts, *([node.module] if node.module else [])])


def _is_project(target: str) -> bool:
    return target.split(".")[0] == PACKAGE


def _is_allowed_library(target: str) -> bool:
    root = target.split(".")[0]
    return root in STDLIB_ALLOWED or root in ALLOWED_LIBRARIES
