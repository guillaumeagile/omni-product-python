from typing import Any

import pytest

from scripts.classement import (
    MARKER,
    SCORECARD,
    equipe_et_regle,
    equipes,
    points_de_la_scorecard,
    rangs,
    render,
)


def scorecard(total: str, login: str = "github-actions") -> dict[str, Any]:
    lignes = [SCORECARD, "## 📊 Scorecard", "", "| Score | Points |", "|---|---:|"]
    body = "\n".join([*lignes, f"| **Total** | **{total}** |", ""])
    return {"author": {"login": login}, "body": body}


def pr(numero: int, branche: str, *commentaires: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": numero,
        "title": f"PR {numero}",
        "headRefName": branche,
        "comments": list(commentaires),
    }


@pytest.mark.parametrize(
    ("branche", "attendu"),
    [
        ("team-red/regle-3-modele-riche", ("team-red", 3)),
        ("bleus/regle-10", ("bleus", 10)),
        ("team-red/regle-3-modele-riche/suite", None),
        ("regle-9-rop", None),
        ("harnais-anneaux", None),
        ("team-red/refacto-ports", None),
    ],
)
def test_la_branche_donne_l_equipe_et_la_regle(
    branche: str, attendu: tuple[str, int] | None
) -> None:
    assert equipe_et_regle(branche) == attendu


def test_les_points_sont_le_total_de_la_derniere_scorecard() -> None:
    assert points_de_la_scorecard([scorecard("+12"), scorecard("-5")]) == -5


def test_une_scorecard_collee_a_la_main_ne_compte_pas() -> None:
    assert points_de_la_scorecard([scorecard("+99", login="tricheur")]) is None


def test_le_score_d_une_equipe_additionne_ses_pr() -> None:
    [rouge] = equipes(
        [
            pr(1, "team-red/regle-1-contexte", scorecard("+10")),
            pr(2, "team-red/regle-2-entite", scorecard("-3")),
            pr(3, "team-red/regle-3-anemique"),
        ]
    )
    assert rouge.score == 7
    assert [m.regle for m in rouge.manches] == [1, 2, 3]


def test_les_pr_hors_convention_ne_jouent_pas() -> None:
    assert equipes([pr(1, "harnais-anneaux", scorecard("+50"))]) == []


def test_les_equipes_a_egalite_partagent_le_rang() -> None:
    classees = equipes(
        [
            pr(1, "verts/regle-1", scorecard("+5")),
            pr(2, "bleus/regle-1", scorecard("+8")),
            pr(3, "rouges/regle-1", scorecard("+5")),
        ]
    )
    assert [e.nom for e in classees] == ["bleus", "rouges", "verts"]
    assert rangs(classees) == [1, 2, 2]


def test_le_classement_en_markdown() -> None:
    texte = render(
        [
            pr(4, "bleus/regle-1-contexte", scorecard("+8")),
            pr(5, "rouges/regle-2-entite"),
        ]
    )
    assert texte.startswith(MARKER)
    assert "| 🥇 1 | bleus | **+8** | 1 |" in texte
    assert "| 🥈 2 | rouges | **0** | 1 |" in texte
    assert "| 2 | #5 | `rouges/regle-2-entite` | ⏳ scorecard en attente |" in texte


def test_un_classement_vide_explique_la_convention() -> None:
    assert "`<equipe>/regle-<N>-<slug>`" in render([])
