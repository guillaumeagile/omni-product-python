"""Lecture des sources pour les règles : un arbre `ast` par fichier, sans rien emprunter aux mesures."""

import ast
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Source:
    module: str
    # Chemin tel qu'il apparaît dans les diagnostics, par exemple `src/omni_product/anemic_model/product.py`.
    path: str
    tree: ast.Module

    @classmethod
    def from_text(cls, module: str, text: str, path: str | None = None) -> "Source":
        return cls(module, path or f"{module.replace('.', '/')}.py", ast.parse(text))


def collect(roots: Sequence[Path], src_root: Path, exclus: Sequence[Path] = ()) -> list[Source]:
    """Les `.py` sous `roots`, hors tests et hors `exclus`, dans l'ordre alphabétique ; `src_root` sert à nommer les modules."""
    paths = sorted(
        {
            path
            for root in roots
            for path in root.rglob("*.py")
            if not _is_test(path) and not any(path.is_relative_to(dossier) for dossier in exclus)
        }
    )
    return [_read(path, src_root) for path in paths]


def _is_test(path: Path) -> bool:
    return path.name.startswith("test_") or "tests" in path.parts


def _read(path: Path, src_root: Path) -> Source:
    relative = path.relative_to(src_root).with_suffix("")
    parts = [part for part in relative.parts if part != "__init__"]
    return Source(
        module=".".join(parts),
        path=path.as_posix(),
        tree=ast.parse(path.read_text(encoding="utf-8")),
    )


def top_level_classes(tree: ast.Module) -> list[ast.ClassDef]:
    return [node for node in tree.body if isinstance(node, ast.ClassDef)]


def public_members(cls: ast.ClassDef) -> Iterator[tuple[str, int, ast.AST | None]]:
    """Les membres déclarés dans la classe, sans les hérités : nom, ligne, et nœud qui porte l'annotation."""
    for stmt in cls.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            yield stmt.target.id, stmt.lineno, stmt
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    yield target.id, target.lineno, None
        elif isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
            yield stmt.name, stmt.lineno, stmt


# Bases dont une classe du modèle a le droit d'hériter : ce sont des outils du langage, pas des variantes du métier.
EXEMPT_BASES = frozenset({"Enum", "StrEnum", "IntEnum", "Protocol", "TypedDict"})


def is_exempt_class(cls: ast.ClassDef) -> bool:
    """Une énumération, un Protocol, un TypedDict ou une exception : exceptés des règles 2 et 4."""
    names = [
        base.id if isinstance(base, ast.Name) else getattr(base, "attr", "") for base in cls.bases
    ]
    return any(name in EXEMPT_BASES or name.endswith(("Error", "Exception")) for name in names)
