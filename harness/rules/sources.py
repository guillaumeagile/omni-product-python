"""Lecture des sources pour les règles : un arbre `ast` par fichier, sans rien emprunter aux mesures."""

import ast
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Source:
    module: str
    tree: ast.Module

    @classmethod
    def from_text(cls, module: str, text: str) -> "Source":
        return cls(module, ast.parse(text))


def collect(roots: Sequence[Path], src_root: Path) -> list[Source]:
    """Les `.py` sous `roots`, hors tests, dans l'ordre alphabétique ; `src_root` sert à nommer les modules."""
    paths = sorted({path for root in roots for path in root.rglob("*.py") if not _is_test(path)})
    return [_read(path, src_root) for path in paths]


def _is_test(path: Path) -> bool:
    return path.name.startswith("test_") or "tests" in path.parts


def _read(path: Path, src_root: Path) -> Source:
    relative = path.relative_to(src_root).with_suffix("")
    parts = [part for part in relative.parts if part != "__init__"]
    return Source.from_text(".".join(parts), path.read_text(encoding="utf-8"))


def top_level_classes(tree: ast.Module) -> list[ast.ClassDef]:
    return [node for node in tree.body if isinstance(node, ast.ClassDef)]
