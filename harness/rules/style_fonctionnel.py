"""Règle 9 (II) : le code va-t-il plus loin vers le fonctionnel, jusqu'à la Railway Oriented Programming ?

Un échec métier est une valeur (règle 5). La règle 9 demande la suite : les étapes s'enchaînent sur le `Result` avec
`.map`, `.and_then` et `.map_err`, sans `if` ni `try` entre elles. À la première erreur, le train bascule sur le rail
d'échec et saute les étapes suivantes. Un `match` exhaustif termine le chemin, à la frontière (un controller qui
traduit le résultat en réponse HTTP).

Cinq constats, du plus proche du ROP au plus général :

- `SF001`, bascule à la main : `.is_ok()`, `.is_err()`, `is_ok(r)`, `isinstance(r, Err)`, ou un `match` dont la
  branche `Err` rend l'erreur telle quelle. Le code refait à la main ce que `.map` et `.and_then` font déjà.
- `SF002`, sortie des rails par exception : `.unwrap()`, `.expect()`, `.unwrap_err()`, `.expect_err()`,
  `.unwrap_or_raise()`. L'échec redevient une exception.
- `SF003`, un `try` qui rattrape : l'échec circule par exception. À la frontière d'une bibliothèque qui lève,
  `@as_result(...)` met l'appel sur les rails.
- `SF005`, un `raise` hors du modèle (controller, service, adaptateur) : l'échec quitte les rails. La fonction rend
  un `Result`, et le controller le traduit en réponse par un `match`. Les `raise` du modèle sont des constats de la
  règle 5 : la règle 9 ne les compte pas une seconde fois.
- `SF004`, un accumulateur dans une boucle (`total += ...`) : `sum`, `any`, `all` ou `functools.reduce` décrivent le
  résultat au lieu des étapes. La boucle qui remplit une liste est déjà un constat de la règle 8 (`PERF401`).

Les `lambda` ne sont pas des constats. Sur une liste, la compréhension reste préférée (règle 8, `C417`). Sur les rails,
une petite `lambda` est bienvenue, et la scorecard compte les « lambdas sur les rails ».

La règle lit tout `omni_product/`, controllers et services compris : le ROP traverse les couches.

Limites : la règle lit la syntaxe, sans les types. `.unwrap()` ou `.is_ok()` sur un autre objet qu'un `Result` est
un constat. `isinstance` et `match` ne sont reconnus que sur `Ok` et `Err` importés de `result`.

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`.
"""

import ast
from dataclasses import dataclass

from harness.rop import MANUAL_SWITCHES, RAISING_EXITS, RESULT_MODULE
from harness.rules.sources import Source, dotted, import_aliases, qualify
from harness.rules.ubiquitous_language import UbiquitousLanguage

MANUAL_SWITCH = "SF001"
RAISING_EXIT = "SF002"
TRY = "SF003"
ACCUMULATOR = "SF004"
RAISE = "SF005"

# Le modèle, où la règle 5 compte déjà les `raise`.
MODEL_PACKAGES = ("omni_product.domain.model", "omni_product.anemic_model")

_RAILS = "enchaîne avec `.map` / `.and_then`, et termine par un `match` exhaustif à la frontière"


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    col: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}:{self.col}: {self.code} {self.message}"


def check(source: Source, language: UbiquitousLanguage) -> list[Finding]:
    """Un constat par écart au style fonctionnel, dans l'ordre des lignes."""
    visitor = _Rails(source)
    visitor.visit(source.tree)
    return sorted(visitor.findings, key=lambda finding: (finding.line, finding.col))


class _Rails(ast.NodeVisitor):
    def __init__(self, source: Source) -> None:
        self._path = source.path
        self._aliases = import_aliases(source.tree)
        self._in_loop = False
        self._in_model = any(
            source.module == package or source.module.startswith(f"{package}.")
            for package in MODEL_PACKAGES
        )
        self.findings: list[Finding] = []

    def visit_Raise(self, node: ast.Raise) -> None:
        if not self._in_model:
            self._report(
                node,
                RAISE,
                "un `raise` fait quitter les rails à l'échec : rends un `Result`, et traduis-le en "
                "réponse par un `match` dans le controller",
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in RAISING_EXITS:
            self._report(
                func, RAISING_EXIT, f"`.{func.attr}()` sort des rails en levant : {_RAILS}"
            )
        elif isinstance(func, ast.Attribute) and func.attr in MANUAL_SWITCHES:
            self._report(func, MANUAL_SWITCH, f"`.{func.attr}()` bascule à la main : {_RAILS}")
        elif self._result_name(func) in MANUAL_SWITCHES:
            self._report(
                func, MANUAL_SWITCH, f"`{ast.unparse(func)}()` bascule à la main : {_RAILS}"
            )
        elif self._is_isinstance_on_case(node):
            self._report(
                node, MANUAL_SWITCH, f"`isinstance` sur `Ok` / `Err` bascule à la main : {_RAILS}"
            )
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        for case in node.cases:
            if self._passes_error_through(node.subject, case):
                self._report(
                    case.pattern,
                    MANUAL_SWITCH,
                    f"la branche `Err` rend l'erreur telle quelle : {_RAILS}",
                )
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self._visit_try(node)

    def visit_TryStar(self, node: ast.TryStar) -> None:
        self._visit_try(node)

    def _visit_try(self, node: ast.Try | ast.TryStar) -> None:
        if node.handlers:
            self._report(
                node,
                TRY,
                "un `try` fait circuler l'échec par exception : `@as_result(...)` met l'appel sur les "
                "rails, puis `.and_then`",
            )
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._visit_loop(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_loop(node)

    def visit_While(self, node: ast.While) -> None:
        self._visit_loop(node)

    def _visit_loop(self, node: ast.For | ast.AsyncFor | ast.While) -> None:
        outer, self._in_loop = self._in_loop, True
        self.generic_visit(node)
        self._in_loop = outer

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_scope(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_scope(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._visit_scope(node)

    def _visit_scope(self, node: ast.AST) -> None:
        """Une fonction définie dans une boucle n'est pas le corps de la boucle."""
        outer, self._in_loop = self._in_loop, False
        self.generic_visit(node)
        self._in_loop = outer

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if self._in_loop and isinstance(node.target, ast.Name):
            self._report(
                node,
                ACCUMULATOR,
                f"`{node.target.id}` accumule dans une boucle : `sum`, `any`, `all` ou "
                "`functools.reduce` décrivent le résultat",
            )
        self.generic_visit(node)

    def _result_name(self, node: ast.expr) -> str | None:
        """Le nom d'un objet de `result` (`Ok`, `Err`, `is_ok`…), sans le module, ou `None`."""
        parts = dotted(node)
        # Le premier nom doit venir d'un import : une variable locale `result` n'est pas le module.
        if parts is None or parts[0] not in self._aliases:
            return None
        qualified = qualify(parts, self._aliases).split(".")
        if qualified[0] != RESULT_MODULE or len(qualified) < 2:
            return None
        return qualified[-1]

    def _is_isinstance_on_case(self, node: ast.Call) -> bool:
        if not (isinstance(node.func, ast.Name) and node.func.id == "isinstance"):
            return False
        if len(node.args) != 2:
            return False
        kinds = node.args[1]
        candidates = kinds.elts if isinstance(kinds, ast.Tuple) else [kinds]
        return any(self._result_name(kind) in {"Ok", "Err"} for kind in candidates)

    def _passes_error_through(self, subject: ast.expr, case: ast.match_case) -> bool:
        """`case Err(): return r`, `case Err() as e: return e`, `case Err(e): return Err(e)`."""
        pattern = case.pattern
        alias = pattern.name if isinstance(pattern, ast.MatchAs) else None
        if isinstance(pattern, ast.MatchAs) and pattern.pattern is not None:
            pattern = pattern.pattern
        if not (isinstance(pattern, ast.MatchClass) and self._result_name(pattern.cls) == "Err"):
            return False
        if len(case.body) != 1 or not isinstance(case.body[0], ast.Return):
            return False
        returned = case.body[0].value
        if isinstance(returned, ast.Name):
            return returned.id == alias or (
                isinstance(subject, ast.Name) and returned.id == subject.id
            )
        captured = _captured(pattern)
        return (
            isinstance(returned, ast.Call)
            and self._result_name(returned.func) == "Err"
            and len(returned.args) == 1
            and isinstance(returned.args[0], ast.Name)
            and returned.args[0].id == captured
        )

    def _report(self, node: ast.expr | ast.stmt | ast.pattern, code: str, message: str) -> None:
        self.findings.append(
            Finding(
                path=self._path,
                line=node.lineno,
                col=node.col_offset + 1,
                code=code,
                message=message,
            )
        )


def _captured(pattern: ast.MatchClass) -> str | None:
    """Le nom capturé par `Err(e)`, ou `None`."""
    if len(pattern.patterns) != 1:
        return None
    inner = pattern.patterns[0]
    return inner.name if isinstance(inner, ast.MatchAs) and inner.pattern is None else None
