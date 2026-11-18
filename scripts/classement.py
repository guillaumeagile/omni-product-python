"""Classement des équipes de l'atelier CUPID, en Markdown.

Entrée : la sortie de `gh pr list --state open --json number,title,headRefName,comments`.

Une PR joue pour une équipe quand sa branche suit la convention `<equipe>/regle-<N>-<slug>`
(par exemple `team-red/regle-3-modele-riche`). Ses points sont le total de la scorecard que la CI
publie en commentaire de la PR. Le score d'une équipe est la somme des points de ses PR ouvertes :
chaque PR est notée par rapport à sa base, l'étape précédente de l'équipe, donc la somme donne
le chemin parcouru depuis `main`.

Le script ne calcule aucun point : il lit le total déjà calculé par la scorecard.
"""

import json
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

MARKER = "<!-- classement-cupid -->"
SCORECARD = "<!-- harness-scorecard -->"
# Seuls les commentaires de la CI comptent : un commentaire collé à la main ne rapporte rien.
AUTEURS_CI = frozenset({"github-actions", "github-actions[bot]", "app/github-actions"})
BRANCHE = re.compile(r"^(?P<equipe>[A-Za-z0-9][A-Za-z0-9_-]*)/regle-(?P<regle>\d+)(?:-[^/]*)?$")
TOTAL = re.compile(r"^\|\s*\*\*Total\*\*\s*\|\s*\*\*([+-]?\d+)\*\*\s*\|\s*$", re.MULTILINE)
MEDAILLES = ("🥇", "🥈", "🥉")


@dataclass(frozen=True)
class Manche:
    """Une PR d'équipe : une règle travaillée, et les points que la scorecard lui donne."""

    numero: int
    titre: str
    branche: str
    equipe: str
    regle: int
    points: int | None


@dataclass(frozen=True)
class Equipe:
    nom: str
    manches: tuple[Manche, ...]

    @property
    def score(self) -> int:
        return sum(m.points or 0 for m in self.manches)


def equipe_et_regle(branche: str) -> tuple[str, int] | None:
    trouve = BRANCHE.match(branche)
    if trouve is None:
        return None
    return trouve["equipe"], int(trouve["regle"])


def auteur(commentaire: Mapping[str, Any]) -> str:
    qui = cast(Mapping[str, Any], commentaire.get("author") or {})
    return str(qui.get("login", ""))


def points_de_la_scorecard(commentaires: Iterable[Mapping[str, Any]]) -> int | None:
    """Le total du dernier commentaire de scorecard publié par la CI, ou None s'il n'y en a pas."""
    totaux = [
        int(trouve[1])
        for c in commentaires
        if auteur(c) in AUTEURS_CI and str(c.get("body", "")).startswith(SCORECARD)
        for trouve in [TOTAL.search(str(c.get("body", "")))]
        if trouve is not None
    ]
    return totaux[-1] if totaux else None


def manche(pr: Mapping[str, Any]) -> Manche | None:
    branche = str(pr.get("headRefName", ""))
    identite = equipe_et_regle(branche)
    if identite is None:
        return None
    commentaires = cast(Sequence[Mapping[str, Any]], pr.get("comments") or [])
    return Manche(
        numero=int(pr["number"]),
        titre=str(pr.get("title", "")),
        branche=branche,
        equipe=identite[0],
        regle=identite[1],
        points=points_de_la_scorecard(commentaires),
    )


def ordre_de_jeu(manche: Manche) -> tuple[int, int]:
    return manche.regle, manche.numero


def equipes(prs: Iterable[Mapping[str, Any]]) -> list[Equipe]:
    """Les équipes, de la meilleure à la moins bonne ; à égalité, par ordre alphabétique."""
    manches = [m for m in map(manche, prs) if m is not None]
    noms = sorted({m.equipe for m in manches})
    toutes = [
        Equipe(nom, tuple(sorted((m for m in manches if m.equipe == nom), key=ordre_de_jeu)))
        for nom in noms
    ]
    return sorted(toutes, key=lambda e: (-e.score, e.nom))


def rangs(classees: Sequence[Equipe]) -> list[int]:
    """Rang de compétition : des équipes à égalité partagent le rang, la suivante saute d'autant."""
    return [1 + sum(1 for autre in classees if autre.score > equipe.score) for equipe in classees]


def signe(points: int) -> str:
    return f"+{points}" if points > 0 else str(points)


def rang_affiche(rang: int) -> str:
    return f"{MEDAILLES[rang - 1]} {rang}" if rang <= len(MEDAILLES) else str(rang)


def points_affiches(manche: Manche) -> str:
    return "⏳ scorecard en attente" if manche.points is None else signe(manche.points)


def render(prs: Iterable[Mapping[str, Any]]) -> str:
    classees = equipes(prs)
    lignes = [MARKER, "# 🏆 Classement de l'atelier CUPID", ""]
    if not classees:
        lignes += [
            "Aucune PR d'équipe ouverte pour le moment.",
            "",
            "Une PR joue quand sa branche s'appelle `<equipe>/regle-<N>-<slug>`.",
        ]
        return "\n".join(lignes) + "\n"

    lignes += [
        "| Rang | Équipe | Score | PR |",
        "|---|---|---:|---:|",
        *(
            f"| {rang_affiche(rang)} | {e.nom} | **{signe(e.score)}** | {len(e.manches)} |"
            for rang, e in zip(rangs(classees), classees, strict=True)
        ),
    ]
    for e in classees:
        lignes += [
            "",
            f"## {e.nom}",
            "",
            "| Règle | PR | Branche | Points |",
            "|---:|---|---|---:|",
            *(
                f"| {m.regle} | #{m.numero} | `{m.branche}` | {points_affiches(m)} |"
                for m in e.manches
            ),
        ]
    lignes += [
        "",
        "_Mis à jour par la CI après chaque scorecard. Les points de chaque PR sont le total de sa "
        "scorecard ; le score d'une équipe est la somme de ses PR ouvertes._",
    ]
    return "\n".join(lignes) + "\n"


def main() -> None:
    prs = cast(list[Mapping[str, Any]], json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    sys.stdout.write(render(prs))


if __name__ == "__main__":
    main()
