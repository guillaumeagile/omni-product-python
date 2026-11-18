"""Complexités cyclomatique (radon) et cognitive (cognitive-complexity).

Ces deux bibliothèques n'ont pas d'annotations : on les isole ici, derrière des fonctions typées.
"""

import ast
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from cognitive_complexity.api import get_cognitive_complexity
from radon.complexity import cc_visit  # pyright: ignore[reportUnknownVariableType]

from harness.metrics.classes import Function, functions_of
from harness.metrics.sources import SourceFile

_cognitive = cast("Callable[[Function], int]", get_cognitive_complexity)
_cyclomatic_blocks = cast("Callable[[str], list[Any]]", cc_visit)  # pyright: ignore[reportUnknownVariableType]


@dataclass(frozen=True)
class FunctionComplexity:
    """Une fonction ou méthode : sa complexité cyclomatique (radon) et sa complexité cognitive."""

    name: str
    cyclomatic: int
    cognitive: int


def measure(source: SourceFile) -> list[FunctionComplexity]:
    """Toutes les fonctions et méthodes du fichier, nommées avec leur classe (`Product.is_expired`).

    Une fonction au corps vide (`...`, `pass`, une docstring seule) compte 0 : c'est une signature, sans chemin à
    tester. C'est le cas des méthodes d'un port (`Protocol`).
    """
    cyclomatic = _cyclomatic_by_name(source.text)
    return [
        FunctionComplexity(
            name,
            0 if _is_empty(function) else cyclomatic.get(name, 1),
            _cognitive(function),
        )
        for name, function in _named_functions(source.tree)
    ]


def _is_empty(function: Function) -> bool:
    return all(_is_placeholder(statement) for statement in function.body)


def _is_placeholder(statement: ast.stmt) -> bool:
    """`pass`, `...` ou une chaîne seule (la docstring)."""
    return isinstance(statement, ast.Pass) or (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and (statement.value.value is Ellipsis or isinstance(statement.value.value, str))
    )


def _cyclomatic_by_name(text: str) -> dict[str, int]:
    """radon rend des blocs `Class` et des blocs `Function` (méthodes comprises) : on ne garde que les seconds."""
    return {
        f"{block.classname}.{block.name}" if block.is_method else str(block.name): int(
            block.complexity
        )
        for block in _cyclomatic_blocks(text)
        if hasattr(block, "is_method")
    }


def _named_functions(tree: ast.Module) -> list[tuple[str, Function]]:
    in_class = {
        id(method): cls.name
        for cls in tree.body
        if isinstance(cls, ast.ClassDef)
        for method in functions_of(cls.body)
    }
    return [
        (f"{in_class[id(fn)]}.{fn.name}" if id(fn) in in_class else fn.name, fn)
        for fn in functions_of(tree.body)
    ]
