"""Lecture des fichiers Python du périmètre mesuré."""

import ast
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceFile:
    """Un fichier source, déjà analysé : son nom de module pointé et son arbre syntaxique."""

    module: str
    is_package: bool
    text: str
    tree: ast.Module

    @classmethod
    def from_text(cls, module: str, text: str, *, is_package: bool = False) -> "SourceFile":
        return cls(module, is_package, text, ast.parse(text))


def collect(roots: Sequence[Path], src_root: Path) -> list[SourceFile]:
    """Tous les `.py` sous `roots`, dans l'ordre alphabétique ; `src_root` sert à retrouver le nom du module."""
    paths = sorted({path for root in roots for path in root.rglob("*.py")})
    return [_read(path, src_root) for path in paths]


def _read(path: Path, src_root: Path) -> SourceFile:
    parts = list(path.relative_to(src_root).with_suffix("").parts)
    is_package = parts[-1] == "__init__"
    if is_package:
        parts.pop()
    return SourceFile.from_text(
        ".".join(parts), path.read_text(encoding="utf-8"), is_package=is_package
    )
