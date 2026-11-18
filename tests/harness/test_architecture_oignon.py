"""La règle 10 : le cœur, reconnu sans nom de répertoire, ne sort pas de l'oignon (AO001, AO002)."""

import textwrap
from pathlib import Path

import pytest

from harness.rules import architecture_oignon, evaluate
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage

# --- Un fichier seul : les imports qui sortent du projet sans être permis ---


def findings(
    text: str, module: str = "omni_product.m.product"
) -> list[architecture_oignon.Finding]:
    source = Source.from_text(module, textwrap.dedent(text))
    return architecture_oignon.check(source, UbiquitousLanguage.load())


def targets(text: str) -> list[str]:
    return [finding.target for finding in findings(text)]


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
    ],
)
def test_a_library_that_touches_the_world_is_a_finding(line: str, target: str) -> None:
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
        "from omni_product.anything.at.all import X",
    ],
)
def test_the_standard_library_result_and_the_project_pass_a_single_file(line: str) -> None:
    assert findings(line) == []


def test_a_library_that_only_starts_like_result_is_not_result() -> None:
    assert targets("import resultat") == ["resultat"]


def test_an_import_under_type_checking_is_still_a_finding() -> None:
    text = """
        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            from sqlalchemy.orm import Session
        """

    [finding] = findings(text)

    assert (finding.line, finding.col, finding.target) == (5, 5, "sqlalchemy.orm")


def test_findings_come_in_line_order_in_ruff_format() -> None:
    text = """
        import requests
        from sqlalchemy import String
        """

    found = findings(text)

    assert [finding.line for finding in found] == [2, 3]
    assert str(found[0]) == (
        "omni_product/m/product.py:2:1: AO001 "
        "`requests` dans le cœur : il dépend d'un port, l'extérieur l'implémente"
    )


def test_one_finding_per_imported_module_of_a_plain_import() -> None:
    assert targets("import os, math, requests") == ["os", "requests"]


# --- Tout le paquet : le cœur reconnu à son contenu et au graphe des imports ---

MODEL = textwrap.dedent(
    """
    from dataclasses import dataclass


    @dataclass(frozen=True)
    class Product:
        name: str
    """
)
# Deux sous-paquets clients : le reste du projet dépend du modèle, qui devient une ancre.
CLIENTS = {
    "web/api.py": "from omni_product.coeur.product import Product\n",
    "stockage/repo.py": "from omni_product.coeur.product import Product\n",
}


def write(tmp_path: Path, files: dict[str, str]) -> Path:
    src = tmp_path / "src"
    for name, text in files.items():
        path = src / "omni_product" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text), encoding="utf-8")
    return src


def rule_10(tmp_path: Path, files: dict[str, str]) -> list[str]:
    """Les constats de la règle 10, sous la forme `fichier:CODE cible`."""
    found = evaluate(write(tmp_path, files))[10]
    return [
        f"{Path(f.path).relative_to(tmp_path / 'src' / 'omni_product')}:{f.code} {f.target}"
        for f in found
        if isinstance(f, architecture_oignon.Finding)
    ]


def test_a_model_with_any_directory_name_is_the_core(tmp_path: Path) -> None:
    files = {"coeur/product.py": MODEL + "\nimport sqlalchemy\n", **CLIENTS}

    assert rule_10(tmp_path, files) == ["coeur/product.py:AO001 sqlalchemy"]


def test_a_model_used_by_a_single_other_package_is_not_an_anchor(tmp_path: Path) -> None:
    files = {
        "coeur/product.py": MODEL + "\nimport sqlalchemy\n",
        "web/api.py": CLIENTS["web/api.py"],
    }

    assert rule_10(tmp_path, files) == []


def test_every_module_of_the_anchor_package_is_in_the_core(tmp_path: Path) -> None:
    files = {"coeur/product.py": MODEL, "coeur/fraicheur.py": "import os\n", **CLIENTS}

    assert rule_10(tmp_path, files) == ["coeur/fraicheur.py:AO001 os"]


def test_a_pure_module_of_another_package_is_an_inner_ring(tmp_path: Path) -> None:
    files = {
        "coeur/product.py": MODEL + "\nfrom omni_product.noyau.ids import ProductId\n",
        "noyau/ids.py": "from dataclasses import dataclass\n",
        **CLIENTS,
    }

    assert rule_10(tmp_path, files) == []


def test_an_impure_module_of_another_package_is_a_finding_at_the_import(tmp_path: Path) -> None:
    files = {
        "coeur/product.py": MODEL + "\nfrom omni_product.adaptateurs.base import Base\n",
        "adaptateurs/base.py": "import sqlalchemy\n",
        **CLIENTS,
    }

    assert rule_10(tmp_path, files) == ["coeur/product.py:AO001 omni_product.adaptateurs.base"]


def test_a_module_that_reaches_a_library_from_afar_is_impure(tmp_path: Path) -> None:
    files = {
        "coeur/product.py": MODEL + "\nfrom omni_product.contrats.horloge import Horloge\n",
        "contrats/horloge.py": "from omni_product.outils.http import client\n",
        "outils/http.py": "import httpx\n",
        **CLIENTS,
    }

    assert rule_10(tmp_path, files) == ["coeur/product.py:AO001 omni_product.contrats.horloge"]


def test_a_module_that_depends_back_on_the_core_is_a_cycle(tmp_path: Path) -> None:
    files = {
        "coeur/product.py": MODEL + "\nfrom omni_product.cas_usage.produits import service\n",
        "cas_usage/produits.py": "from omni_product.coeur.product import Product\n",
        **CLIENTS,
    }

    assert rule_10(tmp_path, files) == ["coeur/product.py:AO002 omni_product.cas_usage.produits"]


def test_a_cycle_inside_the_anchor_package_is_not_a_finding(tmp_path: Path) -> None:
    files = {
        "coeur/product.py": MODEL + "\nfrom omni_product.coeur import supplier\n",
        "coeur/supplier.py": "from omni_product.coeur import product\n",
        **CLIENTS,
    }

    assert rule_10(tmp_path, files) == []


def test_an_unknown_project_module_is_refused(tmp_path: Path) -> None:
    files = {"coeur/product.py": MODEL + "\nfrom omni_product.absent import X\n", **CLIENTS}

    assert rule_10(tmp_path, files) == ["coeur/product.py:AO001 omni_product.absent"]


def test_a_relative_import_is_resolved_against_the_module(tmp_path: Path) -> None:
    files = {
        "coeur/model/product.py": MODEL + "\nfrom ...noyau import ids\nfrom ...infra import db\n",
        "noyau/ids.py": "from dataclasses import dataclass\n",
        "infra/db.py": "import sqlalchemy\n",
        "web/api.py": "from omni_product.coeur.model.product import Product\n",
        "stockage/repo.py": "from omni_product.coeur.model.product import Product\n",
    }

    assert rule_10(tmp_path, files) == ["coeur/model/product.py:AO001 omni_product.infra"]


def test_importing_the_package_counts_for_the_anchor(tmp_path: Path) -> None:
    files = {
        "coeur/__init__.py": "from .product import Product\n",
        "coeur/product.py": MODEL + "\nimport sqlalchemy\n",
        "web/api.py": "from omni_product.coeur import Product\n",
        "stockage/repo.py": "from omni_product.coeur import Product\n",
    }

    assert rule_10(tmp_path, files) == ["coeur/product.py:AO001 sqlalchemy"]


@pytest.mark.parametrize(
    "declaration",
    [
        # Un nom avec un mot technique : un service, un schéma, un format d'échange.
        "class ProductService:\n    pass\n",
        "class ProductSchema:\n    pass\n",
        # Un nom du métier, mais une base prise à une bibliothèque : un format d'échange.
        "from pydantic import BaseModel\n\n\nclass Product(BaseModel):\n    pass\n",
        "from sqlalchemy.orm import DeclarativeBase\n\n\nclass Base(DeclarativeBase):\n    pass\n",
    ],
)
def test_a_class_that_is_not_a_business_concept_makes_no_anchor(
    tmp_path: Path, declaration: str
) -> None:
    files = {"coeur/product.py": declaration + "\nimport sqlalchemy\n", **CLIENTS}

    assert rule_10(tmp_path, files) == []


def test_the_anemic_model_on_an_sqlalchemy_base_is_red(tmp_path: Path) -> None:
    """Le modèle de départ : un `Product` métier sur la base SQLAlchemy du projet."""
    files = {
        "database.py": (
            "from sqlalchemy.orm import DeclarativeBase\n\n\n"
            "class Base(DeclarativeBase):\n    pass\n"
        ),
        "anemic_model/product.py": (
            "from sqlalchemy.orm import Mapped\n\nfrom omni_product.database import Base\n\n\n"
            "class Product(Base):\n    name: Mapped[str]\n"
        ),
        "dal/product_dal.py": "from omni_product.anemic_model.product import Product\n",
        "service/product_service.py": "from omni_product.anemic_model.product import Product\n",
    }

    assert rule_10(tmp_path, files) == [
        "anemic_model/product.py:AO001 sqlalchemy.orm",
        "anemic_model/product.py:AO001 omni_product.database",
    ]
