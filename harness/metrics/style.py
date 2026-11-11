"""Les signaux de style : états mutables, affectations, boucles, lambdas. Ils décrivent, ils ne jugent pas."""

import ast
from dataclasses import dataclass

from harness.metrics.classes import Function, functions_of, top_level_classes
from harness.metrics.sources import SourceFile


@dataclass(frozen=True)
class Style:
    mutable_attributes: int
    assignments: int
    loops: int
    lambdas: int


def measure(sources: list[SourceFile]) -> Style:
    trees = [source.tree for source in sources]
    nodes = [node for tree in trees for node in ast.walk(tree)]
    return Style(
        mutable_attributes=sum(
            mutable_attributes(cls) for tree in trees for cls in top_level_classes(tree)
        ),
        assignments=sum(_is_assignment(node) for node in nodes),
        loops=sum(isinstance(node, ast.For | ast.AsyncFor | ast.While) for node in nodes),
        lambdas=sum(isinstance(node, ast.Lambda) for node in nodes),
    )


def _is_assignment(node: ast.AST) -> bool:
    return isinstance(node, ast.Assign | ast.AugAssign | ast.AnnAssign | ast.NamedExpr)


def mutable_attributes(cls: ast.ClassDef) -> int:
    """Attributs qu'on peut réassigner après la construction.

    Classe `@dataclass(frozen=True)` : aucun. Dataclass ordinaire : tous ses champs.
    Sinon : les `self.x = ...` écrits ailleurs que dans `__init__`.
    """
    decorators = [d for d in cls.decorator_list if _is_dataclass(d)]
    if decorators:
        return 0 if any(_is_frozen(d) for d in decorators) else len(_fields(cls))
    return len(_reassigned_outside_init(cls))


def _is_dataclass(decorator: ast.expr) -> bool:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    return (isinstance(target, ast.Name) and target.id == "dataclass") or (
        isinstance(target, ast.Attribute) and target.attr == "dataclass"
    )


def _is_frozen(decorator: ast.expr) -> bool:
    return isinstance(decorator, ast.Call) and any(
        keyword.arg == "frozen"
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value is True
        for keyword in decorator.keywords
    )


def _fields(cls: ast.ClassDef) -> list[str]:
    return [
        node.target.id
        for node in cls.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    ]


def _reassigned_outside_init(cls: ast.ClassDef) -> set[str]:
    methods: list[Function] = [
        m for m in functions_of(cls.body) if m.name != "__init__" and m.args.args
    ]
    return {
        target.attr
        for method in methods
        for node in ast.walk(method)
        for target in _targets(node)
        if isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == method.args.args[0].arg
    }


def _targets(node: ast.AST) -> list[ast.expr]:
    if isinstance(node, ast.Assign):
        return node.targets
    if isinstance(node, ast.AugAssign | ast.AnnAssign):
        return [node.target]
    return []
