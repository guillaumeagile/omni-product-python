"""La règle 6 : une référence à un effet impur (horloge, hasard, fichier, réseau) est un constat."""

import textwrap

import pytest

from harness.rules import effet_impur
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage


def source(text: str) -> Source:
    return Source.from_text("omni_product.domain.model.product", textwrap.dedent(text))


def findings(text: str) -> list[effet_impur.Finding]:
    return effet_impur.check(source(text), UbiquitousLanguage.load())


def effects_of(text: str) -> list[str]:
    return [finding.effect for finding in findings(text)]


def test_the_clock_in_the_model_is_a_finding():
    text = """
        from datetime import date

        class Product:
            def is_expired(self) -> bool:
                return self.use_by < date.today()
        """

    [finding] = findings(text)

    assert (finding.line, finding.col, finding.code) == (6, 30, effet_impur.CODE)
    assert finding.effect == "datetime.date.today"


@pytest.mark.parametrize(
    ("imports", "expression", "effect"),
    [
        ("import datetime", "datetime.datetime.now()", "datetime.datetime.now"),
        ("import datetime as dt", "dt.datetime.utcnow()", "datetime.datetime.utcnow"),
        ("from datetime import datetime", "datetime.now()", "datetime.datetime.now"),
        ("from datetime import date as d", "d.today()", "datetime.date.today"),
        ("import time", "time.time()", "time.time"),
        ("import uuid", "uuid.uuid4()", "uuid.uuid4"),
        ("from uuid import uuid4", "uuid4()", "uuid.uuid4"),
        ("import random", "random.choice([1, 2])", "random.choice"),
        ("import os", "os.environ.get('HOME')", "os.environ.get"),
        ("import os", "os.getenv('HOME')", "os.getenv"),
        ("import httpx", "httpx.get('http://x')", "httpx.get"),
        ("import requests", "requests.post('http://x')", "requests.post"),
        ("import logging", "logging.getLogger(__name__)", "logging.getLogger"),
    ],
)
def test_an_impure_call_is_seen_through_the_imports_of_the_file(
    imports: str, expression: str, effect: str
):
    text = f"{imports}\n\ndef f():\n    return {expression}\n"

    assert effects_of(text) == [effect]


@pytest.mark.parametrize("call", ["open('f.txt')", "print('x')", "input()"])
def test_a_native_impure_function_is_a_finding(call: str):
    assert effects_of(f"def f():\n    return {call}\n") == [call.split("(")[0]]


def test_a_default_factory_is_a_finding_without_being_called():
    text = """
        from dataclasses import dataclass, field
        from uuid import uuid4

        @dataclass
        class Order:
            id: str = field(default_factory=uuid4)
        """

    assert effects_of(text) == ["uuid.uuid4"]


def test_date_imported_to_type_a_field_is_not_an_effect():
    text = """
        from dataclasses import dataclass
        from datetime import date, datetime

        @dataclass(frozen=True)
        class Perishable:
            sell_by: date
            use_by: date
            recorded_at: datetime
        """

    assert findings(text) == []


def test_a_date_given_as_parameter_is_not_an_effect():
    text = """
        from datetime import date

        class Product:
            def is_expired(self, today: date) -> bool:
                return self.use_by < today
        """

    assert findings(text) == []


def test_a_function_defined_in_the_file_hides_the_native_one():
    text = """
        def print(label: str) -> str:
            return label

        def render() -> str:
            return print("x")
        """

    assert findings(text) == []


def test_a_parameter_named_like_a_native_function_is_not_a_call_to_it():
    text = """
        def parse(input: str) -> int:
            return int(input)
        """

    assert findings(text) == []


def test_every_effect_is_reported_in_line_order():
    text = """
        import uuid
        from datetime import date

        def make():
            first = uuid.uuid4()
            second = date.today()
            return first, second
        """

    assert [(f.line, f.effect) for f in findings(text)] == [
        (6, "uuid.uuid4"),
        (7, "datetime.date.today"),
    ]


def test_the_diagnostic_is_printed_like_a_ruff_one():
    [finding] = findings("import time\n\ndef f():\n    return time.time()\n")

    assert str(finding).startswith(
        f"omni_product/domain/model/product.py:4:12: {effet_impur.CODE} `time.time`"
    )


def test_the_finding_names_the_fix():
    [finding] = findings("import time\n\ndef f():\n    return time.time()\n")

    assert "`Clock`" in finding.message
