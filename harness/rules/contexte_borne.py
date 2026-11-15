"""Règle 1 : chaque classe parle-t-elle d'un seul contexte borné ?

Chaque membre public d'une classe (attribut, méthode, propriété) est rattaché à un contexte par son nom, puis, à
défaut, par les types de ses annotations. Une classe qui touche plusieurs contextes est une violation : il faut
l'éclater, et les liens passent alors par des identifiants.

Les diagnostics suivent le format du compilateur : `chemin:ligne: warning: [catégorie] message`, suivi d'une
`note:` par membre fautif.
"""

import ast
import re
from collections.abc import Iterator
from dataclasses import dataclass

from harness.rules.sources import Source, top_level_classes
from harness.rules.vocabulary import Vocabulary

# Catégorie affichée entre crochets, comme les lint de javac : `warning: [contexte-borne] ...`.
SLUG = "contexte-borne"

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
    cls: str
    members: tuple[Member, ...]

    @property
    def members_by_concern(self) -> dict[str, tuple[str, ...]]:
        grouped: dict[str, list[str]] = {}
        for member in self.members:
            grouped.setdefault(member.concern, []).append(member.name)
        return {concern: tuple(names) for concern, names in grouped.items()}

    def __str__(self) -> str:
        concerns = list(self.members_by_concern)
        lines = [
            f"{self.path}:{self.line}: warning: [{SLUG}] "
            f"'{self.cls}' mêle {len(concerns)} contextes ({', '.join(concerns)})"
        ]
        lines += [
            f"{self.path}:{member.line}: note: '{member.name}' relève du contexte {member.concern}"
            for member in self.members
        ]
        return "\n".join(lines)


def check(source: Source, vocabulary: Vocabulary) -> list[Violation]:
    violations: list[Violation] = []
    for cls in top_level_classes(source.tree):
        members: list[Member] = []
        for name, line, node in _public_members(cls):
            concern = _concern_of(name, node, vocabulary)
            if concern is not None:
                members.append(Member(name, line, concern))
        if len({member.concern for member in members}) >= 2:
            violations.append(
                Violation(path=source.path, line=cls.lineno, cls=cls.name, members=tuple(members))
            )
    return violations


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


def _concern_of(name: str, node: ast.AST | None, vocabulary: Vocabulary) -> str | None:
    if name.startswith("_"):
        return None
    concern = vocabulary.concern_of(name)
    if concern is None and node is not None:
        # Le nom ne dit rien : on regarde les types (paramètres, retour, annotation).
        for annotation in _annotations(node):
            for identifier in _IDENTIFIER.findall(ast.unparse(annotation)):
                concern = vocabulary.concern_of(identifier)
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
