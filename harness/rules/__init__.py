"""Règles de design maison de l'atelier CUPID.

Une règle par module, puis une ligne dans `RULES` : c'est le seul endroit à toucher pour en ajouter une. La scorecard
et `python -m harness.rules` lisent ce registre.

Voir docs/python-regles-de-harnais.md pour la liste et docs/HARNAIS.md pour le dispositif.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from harness.perimetre import dossiers_exclus
from harness.rules import contexte_borne
from harness.rules.points import RuleResult
from harness.rules.sources import Source, collect
from harness.rules.ubiquitous_language import UbiquitousLanguage


@dataclass(frozen=True)
class Rule:
    number: int
    title: str
    # Dossiers à analyser, relatifs à la racine des imports (`src`).
    roots: tuple[str, ...]
    # Rend les constats : une liste vide veut dire que la règle est verte.
    check: Callable[[Source, UbiquitousLanguage], Sequence[object]]
    # Avertissements complémentaires, affichés sans entrer dans les points de la scorecard.
    complement: Callable[[Source, UbiquitousLanguage], Sequence[object]] | None = None


RULES: tuple[Rule, ...] = (
    Rule(
        1,
        "Contexte borné",
        ("omni_product",),
        contexte_borne.check,
        complement=contexte_borne.gaps,
    ),
)


def evaluate(src_root: Path) -> dict[int, list[object]]:
    """Les constats de chaque règle, pour le code tel qu'il est sous `src_root`.

    Une règle dont le dossier n'existe pas (par exemple une base d'avant la restructuration) n'a pas de constat :
    elle est absente du résultat, et la scorecard ne la compare pas.
    """
    return _run(src_root, lambda rule: rule.check)


def complements(src_root: Path) -> dict[int, list[object]]:
    """Les avertissements complémentaires de chaque règle. Ils n'entrent pas dans les points de la scorecard."""
    return _run(src_root, lambda rule: rule.complement)


def _run(
    src_root: Path,
    pick: Callable[[Rule], Callable[[Source, UbiquitousLanguage], Sequence[object]] | None],
) -> dict[int, list[object]]:
    language = UbiquitousLanguage.load()
    output: dict[int, list[object]] = {}
    for rule in RULES:
        check = pick(rule)
        if check is None or not any((src_root / root).is_dir() for root in rule.roots):
            continue
        sources = collect(
            [src_root / root for root in rule.roots], src_root, dossiers_exclus(src_root)
        )
        output[rule.number] = [finding for source in sources for finding in check(source, language)]
    return output


def results(
    head: dict[int, list[object]], base: dict[int, list[object]] | None
) -> tuple[RuleResult, ...]:
    """Croise les constats de la PR et de sa base, règle par règle.

    `before` vaut `None` quand la base n'a pas de constat pour la règle : pas de base, ou règle absente de la base.
    """
    return tuple(
        RuleResult(
            number=rule.number,
            title=rule.title,
            before=None if base is None or rule.number not in base else len(base[rule.number]),
            after=len(head.get(rule.number, [])),
        )
        for rule in RULES
    )
