"""Le score de mutation, lu dans les statistiques que la CI exporte (`mutmut export-cicd-stats`).

La CI publie ces statistiques en artifact `mutation-stats` : celles de la PR, et celles du dernier passage sur `main`,
qui servent de base. La scorecard les reçoit par `--mutation-stats` et `--base-mutation-stats`.
"""

import json
from pathlib import Path


def score(stats_file: str | Path | None) -> float | None:
    """La part des mutants tués, en pourcentage arrondi au dixième. `None` sans fichier lisible ou sans mutant."""
    if stats_file is None:
        return None
    try:
        stats = json.loads(Path(stats_file).read_text(encoding="utf-8"))
        killed, total = int(stats["killed"]), int(stats["total"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return round(killed / total * 100, 1) if total else None
