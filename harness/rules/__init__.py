"""Règles de design maison de l'atelier CUPID.

Une règle par module, puis une ligne dans `RULES` : c'est le seul endroit à toucher pour en ajouter une. La scorecard
et `python -m harness.rules` lisent ce registre.

Voir docs/python-regles-de-harnais.md pour la liste et docs/HARNAIS.md pour le dispositif.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from harness.perimetre import dossiers_exclus
from harness.rules import (
    contexte_borne,
    echec_valeur,
    effet_impur,
    entite_valeur,
    heritage,
    modele_anemique,
)
from harness.rules.points import RuleResult
from harness.rules.sources import Source, collect, collect_tests
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
    # Constats lus dans les fichiers de `tests/` (hors `tests/harness`), ajoutés à ceux du code et comptés avec eux.
    tests: Callable[[Source, UbiquitousLanguage], Sequence[object]] | None = None


RULES: tuple[Rule, ...] = (
    Rule(
        1,
        "Contexte borné",
        ("omni_product",),
        contexte_borne.check,
        complement=contexte_borne.gaps,
    ),
    # La règle 2 ne regarde que le modèle : les adaptateurs et la configuration n'en font pas partie.
    Rule(2, "Entité ou Value Object", ("omni_product/domain/model",), entite_valeur.check),
    # Le modèle est rangé dans domain/model : plus de code sous anemic_model.
    Rule(3, "Pas de modèle anémique", ("omni_product/anemic_model",), modele_anemique.check),
    # Le modèle est là où il est : domain/model, ou anemic_model tant que la règle 3 n'est pas faite.
    Rule(
        4,
        "Composition plutôt qu'héritage",
        ("omni_product/domain/model", "omni_product/anemic_model"),
        heritage.check,
    ),
    # Le modèle, comme la règle 4 : pas de `raise` dans domain/model, ni dans anemic_model tant qu'il y est.
    Rule(
        5,
        "Un échec métier est une valeur",
        ("omni_product/domain/model", "omni_product/anemic_model"),
        echec_valeur.check,
    ),
    # Le modèle, comme les règles 4 et 5 : l'horloge, l'aléatoire, les fichiers et le réseau n'y entrent pas.
    Rule(
        6,
        "Effets impurs hors du cœur",
        ("omni_product/domain/model", "omni_product/anemic_model"),
        effet_impur.check,
        tests=effet_impur.check_tests,
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
        if rule.tests is not None and pick(rule) is rule.check:
            output[rule.number] += _run_tests(src_root, rule.tests, language)
    return output


def _run_tests(
    src_root: Path,
    check: Callable[[Source, UbiquitousLanguage], Sequence[object]],
    language: UbiquitousLanguage,
) -> list[object]:
    """Les constats des fichiers de `tests/`, frère de `src`. Les tests du harnais sont exclus : ils testent le harnais."""
    tests_root = src_root.parent / "tests"
    if not tests_root.is_dir():
        return []
    sources = collect_tests(tests_root, [tests_root / "harness"])
    return [finding for source in sources for finding in check(source, language)]


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
