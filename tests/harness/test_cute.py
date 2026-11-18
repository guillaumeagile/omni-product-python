"""Les jauges CUTE, sur des états dont on change un ingrédient à la fois."""

import textwrap
from dataclasses import replace
from pathlib import Path

import pytest

from harness import cute, scorecard
from harness.metrics.report import measure
from harness.metrics.sources import SourceFile
from harness.rules.contexte_borne import coverage
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage

METRICS = replace(
    measure([SourceFile.from_text("omni_product.domain.product", "class Product:\n    pass\n")]),
    uncle_bob=0.5,
    stability_violations=0,
    max_cyclomatic=7,
    mutable_attributes=10,
)
LEGACY_FINDINGS = {1: 4, 2: 8, 3: 3, 4: 2, 5: 4, 6: 6, 7: 5, 8: 0, 9: 10, 10: 10}
REFERENCE = cute.Reference(findings=LEGACY_FINDINGS, mutable_attributes=10)
LEGACY = cute.State(findings=LEGACY_FINDINGS, metrics=METRICS)
GREEN = dict.fromkeys(LEGACY_FINDINGS, 0)


def test_progress_is_the_share_of_the_way_done():
    assert cute.progress(4, 4) == 0
    assert cute.progress(1, 4) == 0.75
    assert cute.progress(0, 4) == 1
    assert cute.progress(9, 4) == 0, "pire que le legacy : bornée à 0"
    assert cute.progress(0, 0) == 1
    assert cute.progress(2, 0) == 0, "une règle verte au départ qui repasse au rouge"


def test_the_legacy_gauges():
    gauges = cute.gauges(LEGACY, REFERENCE)

    # 🗺️ 0,6 * 0 + 0,4 * (1 - 0,5)
    assert gauges.contextual == 20
    # 🗣️ sans couverture connue : R2 seule
    assert gauges.ubiquitous == 0
    # 🧪 sans mutation : 0,5 * 0 + 0,5 * (10 - 7) / 6
    assert gauges.testable == 25
    # 📖 seule la règle 8 est verte : 0,3 * 1/3
    assert gauges.expressive == 10


def test_all_rules_green_on_a_clean_core_fill_every_gauge():
    metrics = replace(METRICS, uncle_bob=0.0, max_cyclomatic=3, mutable_attributes=0)
    state = cute.State(findings=GREEN, metrics=metrics, mutation=100.0, coverage=1.0)

    assert cute.gauges(state, REFERENCE) == cute.Gauges(100, 100, 100, 100)


def test_a_dependency_violation_caps_contextual_at_fifty():
    metrics = replace(METRICS, uncle_bob=0.0, stability_violations=1)
    state = cute.State(findings=GREEN, metrics=metrics)

    assert cute.gauges(state, REFERENCE).contextual == 50


def test_ubiquitous_mixes_rule_two_and_the_language_coverage():
    state = replace(LEGACY, findings={**LEGACY_FINDINGS, 2: 4}, coverage=0.8)

    assert cute.gauges(state, REFERENCE).ubiquitous == 65  # 0,5 * 0,5 + 0,5 * 0,8


def test_the_mutation_score_weighs_in_testable_when_known():
    with_mutation = replace(LEGACY, mutation=60.0)

    # 0,4 * 0,6 + 0,3 * 0 + 0,3 * 0,5
    assert cute.gauges(with_mutation, REFERENCE).testable == 39


@pytest.mark.parametrize(("cyclomatic", "expected"), [(4, 50), (10, 0), (1, 50), (13, 0)])
def test_simplicity_goes_from_four_paths_to_ten(cyclomatic: int, expected: int):
    state = replace(LEGACY, metrics=replace(METRICS, max_cyclomatic=cyclomatic))

    assert cute.gauges(state, REFERENCE).testable == expected


def test_an_absent_rule_has_no_finding():
    # La règle 3 disparaît avec `anemic_model/` : elle est verte.
    findings = {rule: count for rule, count in LEGACY_FINDINGS.items() if rule != 3}

    state = replace(LEGACY, findings=findings)

    # 0,5 * 1/3 + 0,5 * 0,5
    assert cute.gauges(state, REFERENCE).testable == 42


def test_expressive_counts_fewer_mutable_attributes():
    state = replace(LEGACY, metrics=replace(METRICS, mutable_attributes=5))

    assert cute.gauges(state, REFERENCE).expressive == 25  # 0,1 + 0,3 * 0,5


def test_the_reference_round_trips_through_json(tmp_path: Path):
    path = tmp_path / "reference.json"
    path.write_text(REFERENCE.to_json(), encoding="utf-8")

    assert cute.Reference.load(path) == REFERENCE


def test_the_frozen_reference_covers_every_rule():
    from harness.rules import RULES

    reference = cute.Reference.load()

    assert set(reference.findings) == {rule.number for rule in RULES}


def test_the_language_coverage_counts_attached_and_unknown_members():
    source = Source.from_text(
        "omni_product.domain.product",
        textwrap.dedent(
            """
            class Product:
                id: str
                name: str
                slug: str
                def get_price(self) -> int: ...
                def frobnicate(self) -> None: ...
                def _private(self) -> None: ...
            """
        ),
    )

    # slug et get_price sont rattachés, frobnicate est hors du langage, id et name ne comptent pas.
    assert coverage(source, UbiquitousLanguage.load()) == (2, 3)


def test_the_section_shows_base_then_pr():
    md = cute.section(cute.Gauges(30, 50, 25, 10), cute.Gauges(22, 50, 25, 10))

    assert "### 🌈 CUTE (expérimental)" in md
    assert "🗺️ Contextual   22 →  30  (+8)" in md
    assert "🗣️ Ubiquitous   50 →  50 " in md
    assert "███░░░░░░░" in md
    assert "sans score de mutation" not in md


def test_the_section_says_when_mutation_is_unknown():
    md = cute.section(cute.Gauges(0, 0, 0, 0), None, mutation_known=False)

    assert "🧪 est calculée sans score de mutation." in md


def test_the_scorecard_shows_the_gauges_after_the_other_tables():
    card = scorecard.render(
        METRICS, METRICS, rules_md="### 🧪 Règles du harnais\n", cute_md="### 🌈 CUTE\n"
    )

    assert card.index("🧪 Règles du harnais") < card.index("📏 Métriques") < card.index("🌈 CUTE")
    assert card.index("**Les couches**") < card.index("🌈 CUTE") < card.index("<sub>Périmètre")
    assert "<details>" not in card
