"""Règle 1 : chaque classe parle-t-elle d'un seul contexte borné ?

Chaque membre public d'une classe (attribut, méthode, propriété) est rattaché à un contexte par son nom, puis, à
défaut, par les types de ses annotations. Une classe qui touche plusieurs contextes est une violation : il faut
l'éclater, et les liens passent alors par des identifiants.
"""

import ast
import re
from collections.abc import Iterator
from dataclasses import dataclass

from harness.rules.sources import Source, top_level_classes
from harness.rules.vocabulary import Vocabulary

_IDENTIFIER = re.compile(r"[A-Za-z_]\w*")


@dataclass(frozen=True)
class Violation:
    module: str
    line: int
    cls: str
    members_by_concern: dict[str, tuple[str, ...]]

    def __str__(self) -> str:
        contexts = " + ".join(self.members_by_concern)
        detail = " ; ".join(
            f"{concern} : {', '.join(members)}"
            for concern, members in self.members_by_concern.items()
        )
        return f"{self.module}:{self.line} {self.cls} touche {contexts} ({detail})"


def check(source: Source, vocabulary: Vocabulary) -> list[Violation]:
    violations: list[Violation] = []
    for cls in top_level_classes(source.tree):
        members_by_concern: dict[str, list[str]] = {}
        for name, node in _public_members(cls):
            concern = _concern_of(name, node, vocabulary)
            if concern is not None:
                members_by_concern.setdefault(concern, []).append(name)
        if len(members_by_concern) >= 2:
            violations.append(
                Violation(
                    module=source.module,
                    line=cls.lineno,
                    cls=cls.name,
                    members_by_concern={
                        concern: tuple(members) for concern, members in members_by_concern.items()
                    },
                )
            )
    return violations


def _public_members(cls: ast.ClassDef) -> Iterator[tuple[str, ast.AST | None]]:
    for stmt in cls.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            yield stmt.target.id, stmt
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    yield target.id, None
        elif isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
            yield stmt.name, stmt


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
