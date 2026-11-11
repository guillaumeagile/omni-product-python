"""Le coût de lecture : les tokens, comptés comme le ferait un modèle de langage (`o200k_base`).

On ne compte que le **code efficace** : ni commentaires, ni docstrings, ni mise en forme. Pour cela, on relit
l'arbre syntaxique et on le réécrit (`ast.unparse`) avant de compter.
"""

import ast
from collections.abc import Callable
from functools import cache

import tiktoken


@cache
def _encoder() -> Callable[[str], list[int]]:
    encoding = tiktoken.get_encoding("o200k_base")

    def encode(text: str) -> list[int]:
        return encoding.encode(text, disallowed_special=())

    return encode


def count(text: str) -> int:
    return len(_encoder()(text))


def effective_code(tree: ast.Module) -> str:
    """Le code sans commentaires (ils n'existent pas dans l'arbre) ni docstrings, normalisé."""
    stripped = _DocstringStripper().visit(ast.parse(ast.unparse(tree)))
    return ast.unparse(ast.fix_missing_locations(stripped))


class _DocstringStripper(ast.NodeTransformer):
    def visit_Module(self, node: ast.Module) -> ast.Module:
        return self._strip(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        return self._strip(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        return self._strip(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        return self._strip(node)

    def _strip[N: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef](
        self, node: N
    ) -> N:
        self.generic_visit(node)
        body = node.body
        if body and isinstance(body[0], ast.Expr) and _is_string(body[0].value):
            node.body = body[1:] or [ast.Pass()]
        return node


def _is_string(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)
