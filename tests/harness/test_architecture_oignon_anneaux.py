"""La règle 10 : le noyau et les ports sont des anneaux de l'oignon (AO001)."""

import textwrap

import pytest

from harness.rules import architecture_oignon
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage


def targets(text: str, module: str) -> list[str]:
    source = Source.from_text(module, textwrap.dedent(text), None)
    return [f.target for f in architecture_oignon.check(source, UbiquitousLanguage.load())]


@pytest.mark.parametrize(
    ("module", "line", "target"),
    [
        (
            "omni_product.kernel.ids",
            "from omni_product.domain.model import X",
            "omni_product.domain.model",
        ),
        (
            "omni_product.kernel.ids",
            "from omni_product.ports.clock import Clock",
            "omni_product.ports.clock",
        ),
        ("omni_product.ports.clock", "from omni_product.kernel.ids import ProductId", None),
        (
            "omni_product.ports.supplier",
            "from omni_product.domain.model import Supplier",
            "omni_product.domain.model",
        ),
        ("omni_product.ports.supplier", "import sqlalchemy", "sqlalchemy"),
        (
            "omni_product.domain.model.product",
            "from omni_product.kernel.ids import ProductId",
            None,
        ),
        ("omni_product.domain.model.product", "from omni_product.ports.clock import Clock", None),
        (
            "omni_product.domain.model.product",
            "from omni_product.service.x import Y",
            "omni_product.service.x",
        ),
    ],
)
def test_each_ring_imports_only_what_it_may(module: str, line: str, target: str | None) -> None:
    found = targets(line, module)
    assert found == ([] if target is None else [target])


def test_a_module_outside_the_onion_is_not_checked() -> None:
    assert targets("import sqlalchemy", "omni_product.service.product_service") == []
