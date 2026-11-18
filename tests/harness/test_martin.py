"""Les métriques de Robert Martin par couche, sur un petit projet dont on connaît la réponse."""

import ast
import textwrap

from harness import scorecard
from harness.metrics import martin
from harness.metrics.report import measure
from harness.metrics.sources import SourceFile


def source(module: str, text: str = "", *, is_package: bool = False) -> SourceFile:
    return SourceFile.from_text(module, textwrap.dedent(text), is_package=is_package)


# domain : un port et une entité, n'importe rien du projet.
# infrastructure : implémente le port, importe domain.
# main : assemble, importe infrastructure et domain.
PROJECT = [
    source(
        "omni_product.domain.port",
        """
        from typing import Protocol

        class Repository(Protocol):
            def save(self, item: object) -> None: ...
        """,
    ),
    source(
        "omni_product.domain.product",
        """
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Product:
            name: str
        """,
    ),
    source(
        "omni_product.infrastructure.memory",
        """
        from omni_product.domain.port import Repository
        from ..domain.product import Product

        class MemoryRepository:
            def save(self, item: Product) -> None: ...
        """,
    ),
    source(
        "omni_product.main",
        """
        from omni_product import infrastructure
        import omni_product.domain.product
        """,
    ),
]


def by_name(sources: list[SourceFile]) -> dict[str, martin.LayerMetrics]:
    return {layer.name: layer for layer in martin.measure(sources)}


def test_a_stable_layer_half_abstract_is_halfway_from_the_main_sequence():
    domain = by_name(PROJECT)["domain"]

    assert (domain.modules, domain.classes, domain.abstract_classes) == (2, 2, 1)
    assert (domain.afferent, domain.efferent) == (2, 0)
    assert domain.instability == 0.0
    assert domain.abstractness == 0.5
    assert domain.distance == 0.5
    assert domain.depends_on == ()


def test_links_have_a_direction():
    layers = by_name(PROJECT)

    assert layers["infrastructure"].depends_on == ("domain",)
    assert (layers["infrastructure"].afferent, layers["infrastructure"].efferent) == (1, 1)
    assert layers["infrastructure"].instability == 0.5
    assert layers["main"].depends_on == ("domain", "infrastructure")
    assert (layers["main"].afferent, layers["main"].efferent) == (0, 1)
    assert layers["main"].instability == 1.0
    assert layers["main"].distance == 0.0


def test_imports_inside_a_layer_are_not_links():
    domain = by_name(
        [
            source("omni_product.domain.a", "from omni_product.domain.b import B\n"),
            source("omni_product.domain.b", "class B: ...\n"),
        ]
    )["domain"]

    assert (domain.afferent, domain.efferent) == (0, 0)
    assert domain.instability is None
    assert domain.distance is None


def test_a_layer_of_functions_still_has_links():
    layers = by_name(
        [
            source("omni_product.dal.product_dal", "from omni_product.anemic_model import P\n"),
            source("omni_product.anemic_model", "class P: ...\n", is_package=True),
        ]
    )

    assert layers["dal"].classes == 0
    assert layers["dal"].abstractness == 0.0
    assert layers["dal"].efferent == 1
    assert layers["anemic_model"].afferent == 1


def test_abstract_classes_are_ports_abcs_and_abstract_methods():
    tree = source(
        "omni_product.domain.x",
        """
        import abc
        import typing
        from abc import ABC, abstractmethod

        class P(typing.Protocol[T]): ...
        class B(ABC): ...
        class M(metaclass=abc.ABCMeta): ...
        class S:
            @abstractmethod
            def f(self): ...
        class Concrete: ...
        """,
    ).tree

    flags = [martin.is_abstract(node) for node in tree.body if isinstance(node, ast.ClassDef)]

    assert flags == [True, True, True, True, False]


def test_mean_distance_weights_layers_by_their_modules_and_skips_unlinked_ones():
    # domain : D 0.5 sur 2 modules ; infrastructure : D 0.5 sur 1 ; main : D 0 sur 1.
    assert martin.mean_distance(martin.measure(PROJECT)) == round((0.5 * 2 + 0.5 + 0) / 4, 2)


def test_mean_distance_is_zero_without_any_link():
    assert (
        martin.mean_distance(martin.measure([source("omni_product.domain.a", "class A: ...\n")]))
        == 0.0
    )


def test_the_report_and_the_scorecard_carry_the_mean_distance():
    metrics = measure(PROJECT)

    assert metrics.distance == 0.38
    assert "| Distance des couches (D moyen, 0 = le mieux) | | 0.38 | | |" in scorecard.render(
        metrics, None
    )
    assert "Fan-out (total)" not in scorecard.render(metrics, None)
    assert "CBO (total)" not in scorecard.render(metrics, None)


def test_outside_the_project_has_no_layer():
    assert martin.layer_of("omni_product") is None
    assert martin.layer_of("sqlalchemy.orm") is None
    assert martin.layer_of("omni_product.domain.model.product") == "domain"


def test_scorecard_shows_layers_from_base_to_pr():
    card = scorecard.render(measure(PROJECT), measure(PROJECT[:2]))

    assert "| Couche | Ca | Ce | I | A | D | Dépend de |" in card
    assert "| `domain` | 0 → 2 | 0 | n/a → 0 | 0.5 | n/a → 0.5 | — |" in card
    assert "| `infrastructure` | 1 | 1 | 0.5 | 0 | 0.5 | `domain` |" in card
