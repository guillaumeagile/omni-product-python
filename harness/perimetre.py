"""Le périmètre analysé par le harnais : tout `omni_product/`, sauf les couches hors du cœur.

Les règles et les mesures lisent les mêmes fichiers. Ce module est le seul endroit qui dit lesquels.
Les tests ne sont jamais dans le périmètre : `collect` les écarte déjà.
"""

from pathlib import Path

PACKAGE = "omni_product"
# Sous-paquets et modules de `omni_product/` exclus du périmètre : les couches et la plomberie qui ne sont pas le cœur.
HORS_PERIMETRE = ("controller", "service", "dal", "config.py", "database.py")


def dossiers_exclus(src_root: Path) -> list[Path]:
    """Les dossiers et fichiers à écarter, sous la racine des imports (`src`)."""
    return [src_root / PACKAGE / name for name in HORS_PERIMETRE]
