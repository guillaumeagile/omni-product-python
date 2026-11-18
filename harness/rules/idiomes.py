"""Règle 8 : le code s'écrit-il avec les idiomes courants de Python ?

Pas de code maison : ruff porte la vérification, avec la sélection durcie `PERF`, `C4`, `SIM`, `UP` et `C90`. Chaque
diagnostic de ruff dans le modèle est un constat : une boucle qui remplit une liste (`PERF401`), une chaîne de `if`
(`SIM116`), une fonction trop complexe (`C901`).

Les diagnostics suivent le format de ruff : `chemin:ligne:colonne: CODE message`. Le harnais les reprend tels quels.
"""

import re
import subprocess
import sys
from dataclasses import dataclass

from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage

SELECT = "PERF,C4,SIM,UP,C90"

_LINE = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+):(?P<col>\d+): (?P<code>[A-Z]+\d+) (?P<message>.*)$"
)


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
    """Les diagnostics de ruff sur le fichier de `source`. Une liste vide veut dire que la règle est verte."""
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--select",
            SELECT,
            "--output-format",
            "concise",
            "--no-cache",
            source.path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    findings: list[Finding] = []
    for line in completed.stdout.splitlines():
        match = _LINE.match(line)
        if match is None:
            continue
        findings.append(
            Finding(
                path=match["path"],
                line=int(match["line"]),
                col=int(match["col"]),
                code=match["code"],
                message=match["message"],
            )
        )
    return findings
