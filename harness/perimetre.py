"""Le périmètre analysé par le harnais : tout `omni_product/`, sauf `controller/`, `service/` et la plomberie.

Les règles et les mesures lisent les mêmes fichiers, à une exception près : la règle 9 (style fonctionnel, ROP) lit tout
le paquet. Ce module est le seul endroit qui dit lesquels.
Les tests ne sont jamais dans le périmètre : `collect` les écarte déjà.
"""

from pathlib import Path

PACKAGE = "omni_product"
# Sous-paquets et modules de `omni_product/` exclus du périmètre.
# `dal/` est mesuré : la persistance qu'il porte se déplace vers `infrastructure/` (règle 10), et l'exclure ferait
# compter ce déplacement comme du code ajouté.
# `config.py` et `database.py` sont de la plomberie : l'architecture en oignon (règle 10) les sortira du cœur.
HORS_PERIMETRE = ("controller", "service", "config.py", "database.py")
# La règle 9 n'exclut rien : un controller ou un service s'écrit en ROP comme le cœur, le style ne dépend pas de la couche.
TOUT_LE_PAQUET: tuple[str, ...] = ()


def dossiers_exclus(src_root: Path, hors: tuple[str, ...] = HORS_PERIMETRE) -> list[Path]:
    """Les dossiers et fichiers à écarter, sous la racine des imports (`src`)."""
    return [src_root / PACKAGE / name for name in hors]


def description() -> str:
    """Le périmètre en une phrase, lue depuis `HORS_PERIMETRE` pour ne pas dériver."""
    exclus = ", ".join(
        f"`{name}/`" if not name.endswith(".py") else f"`{name}`" for name in HORS_PERIMETRE
    )
    return f"`{PACKAGE}/`, hors {exclus}"
