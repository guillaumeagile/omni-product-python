"""Règle 1 : chaque classe parle-t-elle d'un seul contexte borné ?

Chaque membre public d'une classe (attribut, méthode, propriété) est rattaché à un contexte par son nom, puis, à
défaut, par les types de ses annotations. Les membres hérités des classes du même module comptent aussi.
Un identifiant (`id`, `product_id`, `tvaId`) ne porte pas de contexte : il dit seulement quelle entité est visée.
Une classe qui touche plusieurs contextes est une violation : il faut l'éclater.

Complément (`gaps`) : un membre qui ne rattache à aucun contexte, et dont les mots ne sont ni génériques ni
des liens, est un mot hors ubiquitous language. C'est un trou du fichier, pas une violation : il ne compte pas dans les points.

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`, une ligne par classe fautive.
"""

import ast
import re
from collections.abc import Iterator
from dataclasses import dataclass

from harness.rules.sources import Source, top_level_classes
from harness.rules.ubiquitous_language import UbiquitousLanguage, words

# Code affiché en tête de message, comme ruff : `CB001 ...` (CB pour « contexte borné »).
CODE = "CB001"
# Complément : mots hors ubiquitous language. Il ne compte pas dans les points de la scorecard.
GAP_CODE = "CB002"

_IDENTIFIER = re.compile(r"[A-Za-z_]\w*")


@dataclass(frozen=True)
class Member:
    name: str
    line: int
    concern: str


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    col: int
    cls: str
    members: tuple[Member, ...]

    @property
    def members_by_concern(self) -> dict[str, tuple[str, ...]]:
        grouped: dict[str, list[str]] = {}
        for member in self.members:
            grouped.setdefault(member.concern, []).append(member.name)
        return {concern: tuple(names) for concern, names in grouped.items()}

    def __str__(self) -> str:
        details = ", ".join(f"{member.name} ({member.concern})" for member in self.members)
        concerns = len(self.members_by_concern)
        return (
            f"{self.path}:{self.line}:{self.col}: {CODE} "
            f"'{self.cls}' mêle {concerns} contextes : {details}"
        )


def check(source: Source, language: UbiquitousLanguage) -> list[Violation]:
    violations: list[Violation] = []
    classes = {cls.name: cls for cls in top_level_classes(source.tree)}
    for cls in classes.values():
        members = _members_of(cls, classes, language)
        if len({member.concern for member in members}) >= 2:
            violations.append(
                Violation(
                    path=source.path,
                    line=cls.lineno,
                    col=cls.col_offset + 1,
                    cls=cls.name,
                    members=tuple(members),
                )
            )
    return violations


def _members_of(
    cls: ast.ClassDef,
    classes: dict[str, ast.ClassDef],
    language: UbiquitousLanguage,
    seen: frozenset[str] = frozenset(),
) -> list[Member]:
    """Les membres de la classe, hérités compris. Un membre redéfini garde la version de la sous-classe."""
    found: dict[str, Member] = {}
    for base in _base_names(cls):
        # `seen` évite de boucler si deux classes s'étendent mutuellement.
        if base in classes and base not in seen:
            for member in _members_of(classes[base], classes, language, seen | {cls.name}):
                found[member.name] = member
    for name, line, node in _public_members(cls):
        concern = _concern_of(name, node, language)
        if concern is not None:
            found[name] = Member(name, line, concern)
    return list(found.values())


def _base_names(cls: ast.ClassDef) -> Iterator[str]:
    for base in cls.bases:
        if isinstance(base, ast.Name):
            yield base.id


def _public_members(cls: ast.ClassDef) -> Iterator[tuple[str, int, ast.AST | None]]:
    for stmt in cls.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            yield stmt.target.id, stmt.lineno, stmt
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    yield target.id, target.lineno, None
        elif isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
            yield stmt.name, stmt.lineno, stmt


def _concern_of(name: str, node: ast.AST | None, language: UbiquitousLanguage) -> str | None:
    if name.startswith("_") or language.is_identifier(name):
        return None
    concern = language.concern_of(name)
    if concern is None and node is not None:
        # Le nom ne dit rien : on regarde les types (paramètres, retour, annotation).
        for annotation in _annotations(node):
            for identifier in _IDENTIFIER.findall(ast.unparse(annotation)):
                concern = language.concern_of(identifier)
                if concern is not None:
                    return concern
    return concern


def _annotations(node: ast.AST) -> Iterator[ast.expr]:
    if isinstance(node, ast.AnnAssign):
        yield node.annotation
    elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        for argument in arguments:
            if argument.annotation is not None:
                yield argument.annotation
        if node.returns is not None:
            yield node.returns


@dataclass(frozen=True)
class Gap:
    path: str
    line: int
    col: int
    cls: str
    # Pour chaque membre fautif : son nom et ses mots hors ubiquitous language.
    unknown: tuple[tuple[str, tuple[str, ...]], ...]

    def __str__(self) -> str:
        details = ", ".join(f"{name} ({' '.join(parts)})" for name, parts in self.unknown)
        return (
            f"{self.path}:{self.line}:{self.col}: {GAP_CODE} "
            f"'{self.cls}' a des mots hors ubiquitous language : {details}"
        )


def gaps(source: Source, language: UbiquitousLanguage) -> list[Gap]:
    """Les membres propres à chaque classe que ni le nom ni les types ne rattachent à un contexte.

    Seuls les mots non génériques comptent : `id`, `get`, `name` ne sont pas des trous de l'ubiquitous language.
    Les membres hérités ne sont pas repris : ils sont signalés dans leur classe d'origine.
    """
    found: list[Gap] = []
    for cls in top_level_classes(source.tree):
        unknown: list[tuple[str, tuple[str, ...]]] = []
        for name, _line, node in _public_members(cls):
            if name.startswith("_") or language.is_identifier(name):
                continue
            if _concern_of(name, node, language) is not None:
                continue
            leftover = tuple(word for word in words(name) if not language.is_generic(word))
            if leftover:
                unknown.append((name, leftover))
        if unknown:
            found.append(Gap(source.path, cls.lineno, cls.col_offset + 1, cls.name, tuple(unknown)))
    return found
