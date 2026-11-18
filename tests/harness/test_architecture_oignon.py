"""La règle 10 : le cœur n'importe que lui-même, la bibliothèque standard et `result` (AO001)."""

import textwrap
from pathlib import Path

import pytest

from harness.rules import architecture_oignon, evaluate
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage


def findings(
    text: str, module: str = "omni_product.domain.model.product", path: str | None = None
) -> list[architecture_oignon.Finding]:
    source = Source.from_text(module, textwrap.dedent(text), path)
    return architecture_oignon.check(source, UbiquitousLanguage.load())


def targets(text: str, **kwargs: str) -> list[str]:
    return [finding.target for finding in findings(text, **kwargs)]


@pytest.mark.parametrize(
    ("line", "target"),
    [
        ("from sqlalchemy.orm import Session", "sqlalchemy.orm"),
        ("import sqlalchemy", "sqlalchemy"),
        ("import fastapi as api", "fastapi"),
        ("import requests", "requests"),
        ("import os", "os"),
        ("from time import sleep", "time"),
        ("import sys", "sys"),
        ("import random", "random"),
        ("import json", "json"),
        ("from pathlib import Path", "pathlib"),
        ("import logging", "logging"),
        ("import sqlite3", "sqlite3"),
        ("from omni_product.database import Base", "omni_product.database"),
        (
            "from omni_product.service.product_service import X",
            "omni_product.service.product_service",
        ),
        ("from omni_product.dal import product_dal", "omni_product.dal"),
        (
            "from omni_product.exception.business_exception import X",
            "omni_product.exception.business_exception",
        ),
        (
            "from omni_product.infrastructure.adapter import X",
            "omni_product.infrastructure.adapter",
        ),
    ],
)
def test_an_import_that_leaves_the_core_is_a_finding(line: str, target: str) -> None:
    assert targets(line) == [target]


@pytest.mark.parametrize(
    "line",
    [
        "from dataclasses import dataclass",
        "import datetime",
        "import uuid",
        "from decimal import Decimal",
        "from enum import Enum",
        "from collections.abc import Sequence",
        "import functools",
        "from typing import Protocol",
        "from __future__ import annotations",
        "from result import Err, Ok",
        "import result",
        "from omni_product.domain.model.transport_request import TransportRequest",
        "from omni_product.domain.port.transport_carbon_port import TransportCarbonPort",
        "from omni_product.anemic_model.supplier import Supplier",
    ],
)
def test_the_core_the_standard_library_and_result_are_allowed(line: str):
    assert findings(line) == []


def test_a_package_that_only_starts_like_the_core_is_not_the_core():
    assert targets("import omni_product.domainx.thing") == ["omni_product.domainx.thing"]
    assert targets("import resultat") == ["resultat"]


def test_an_import_under_type_checking_is_still_a_finding():
    text = """
        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            from sqlalchemy.orm import Session
        """

    [finding] = findings(text)

    assert (finding.line, finding.col, finding.target) == (5, 5, "sqlalchemy.orm")


def test_a_relative_import_is_resolved_against_the_module():
    # Depuis domain.model.product : `..port` reste dans le cœur, `...service` en sort.
    assert findings("from ..port import transport_carbon_port") == []
    assert targets("from ...service import product_service") == ["omni_product.service"]


def test_a_relative_import_in_an_init_file_starts_from_the_package_itself():
    text = "from .product import Product\nfrom ...dal import product_dal"

    found = targets(
        text, module="omni_product.domain.model", path="src/omni_product/domain/model/__init__.py"
    )

    assert found == ["omni_product.dal"]


def test_a_dot_import_names_the_imported_module():
    assert targets("from . import sibling") == []
    assert targets("from .. import port") == []
    assert targets("from ... import service") == ["omni_product.service"]


def test_findings_come_in_line_order_in_ruff_format():
    text = """
        import requests
        from sqlalchemy import String
        """

    found = findings(text)

    assert [finding.line for finding in found] == [2, 3]
    assert str(found[0]) == (
        "omni_product/domain/model/product.py:2:1: AO001 "
        "`requests` dans le cœur : il dépend d'un port, l'extérieur l'implémente"
    )


def test_one_finding_per_imported_module_of_a_plain_import():
    assert targets("import os, math, requests") == ["os", "requests"]


def test_evaluate_reads_the_core_and_ignores_the_outside(tmp_path: Path):
    root = tmp_path / "src" / "omni_product"
    (root / "domain" / "model").mkdir(parents=True)
    (root / "service").mkdir()
    (root / "domain" / "model" / "a.py").write_text("import requests\n")
    (root / "service" / "b.py").write_text("import requests\n")

    found = evaluate(tmp_path / "src")[10]

    assert [str(finding).split(":")[0] for finding in found] == [
        (root / "domain" / "model" / "a.py").as_posix()
    ]


def write_core(tmp_path: Path, text: str) -> Path:
    module = tmp_path / "src" / "omni_product" / "domain" / "model" / "product.py"
    module.parent.mkdir(parents=True)
    module.write_text(textwrap.dedent(text))
    return tmp_path / "src"


def test_a_core_that_raises_the_business_exception_is_red(tmp_path: Path):
    """Le modèle découpé (règles 2 à 5) : SQLAlchemy est sorti, l'exception métier reste."""
    src = write_core(
        tmp_path,
        """
        from dataclasses import dataclass

        from omni_product.exception.business_exception import BusinessException
        """,
    )

    [finding] = [str(finding) for finding in evaluate(src)[10]]

    assert "AO001 `omni_product.exception.business_exception` dans le cœur" in finding


def test_a_core_whose_failures_are_values_is_green(tmp_path: Path):
    """La règle 10 corrigée : l'échec métier est une valeur `Result`, le cœur ne sort plus."""
    src = write_core(
        tmp_path,
        """
        from dataclasses import dataclass

        from result import Err, Ok, Result

        from omni_product.domain.model.transport_request import TransportRequest
        """,
    )

    assert evaluate(src)[10] == []
