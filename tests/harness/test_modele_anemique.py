"""La règle 3 : plus de code sous anemic_model/, et la règle 2 ne regarde que domain/model/."""

import textwrap

from harness.rules import RULES, modele_anemique
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage


def source(text: str, module: str = "omni_product.anemic_model.product") -> Source:
    return Source.from_text(module, textwrap.dedent(text))


def test_any_non_empty_module_under_anemic_model_is_a_finding():
    [finding] = modele_anemique.check(source("class Product: ...\n"), UbiquitousLanguage.load())

    assert finding.code == modele_anemique.CODE
    assert "omni_product.anemic_model.product" in finding.message


def test_an_empty_module_under_anemic_model_is_not_a_finding():
    assert modele_anemique.check(source(""), UbiquitousLanguage.load()) == []


def test_the_registry_has_rules_1_to_8_and_10_on_the_expected_scopes():
    # Régression : la règle 2 a été perdue à une fusion, sans que rien ne le signale.
    roots = {rule.number: rule.roots for rule in RULES}

    assert roots == {
        1: ("omni_product",),
        2: ("omni_product/domain/model",),
        3: ("omni_product/anemic_model",),
        4: ("omni_product/domain/model", "omni_product/anemic_model"),
        5: ("omni_product/domain/model", "omni_product/anemic_model"),
        6: ("omni_product/domain/model", "omni_product/anemic_model"),
        7: ("omni_product/domain/model", "omni_product/anemic_model"),
        8: ("omni_product",),
        10: ("omni_product/domain", "omni_product/anemic_model"),
    }
