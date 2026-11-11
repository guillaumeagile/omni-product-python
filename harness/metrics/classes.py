"""Ce que les mesures de cohésion et de couplage lisent dans une classe."""

import ast
from collections.abc import Iterator

type Function = ast.FunctionDef | ast.AsyncFunctionDef

# Ces méthodes ne disent rien de la cohésion : le constructeur initialise tout, par construction.
_EXCLUDED_NAMES = frozenset({"__init__", "__new__"})
_EXCLUDED_DECORATORS = frozenset({"staticmethod", "classmethod"})


def top_level_classes(tree: ast.Module) -> list[ast.ClassDef]:
    return [node for node in tree.body if isinstance(node, ast.ClassDef)]


def functions_of(body: list[ast.stmt]) -> Iterator[Function]:
    """Les fonctions de module et les méthodes de classe (pas les fonctions imbriquées : elles comptent dans leur parent)."""
    for node in body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            yield node
        elif isinstance(node, ast.ClassDef):
            yield from functions_of(node.body)


def _methods(cls: ast.ClassDef) -> list[Function]:
    return [node for node in cls.body if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)]


def instance_methods(cls: ast.ClassDef) -> list[Function]:
    """Les méthodes d'instance, hors constructeur : celles dont on mesure la cohésion."""
    return [method for method in _methods(cls) if _is_measured(method)]


def _is_measured(method: Function) -> bool:
    decorators = {d.id for d in method.decorator_list if isinstance(d, ast.Name)}
    return method.name not in _EXCLUDED_NAMES and not decorators & _EXCLUDED_DECORATORS


def attributes_by_method(cls: ast.ClassDef) -> list[frozenset[str]]:
    """Pour chaque méthode d'instance, les attributs de `self` qu'elle lit ou écrit (hors méthodes de la classe)."""
    method_names = {method.name for method in _methods(cls)}
    return [_self_attributes(method) - method_names for method in instance_methods(cls)]


def _self_attributes(method: Function) -> frozenset[str]:
    arguments = [*method.args.posonlyargs, *method.args.args]
    if not arguments:
        return frozenset()
    receiver = arguments[0].arg
    return frozenset(
        node.attr
        for node in ast.walk(method)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == receiver
    )
