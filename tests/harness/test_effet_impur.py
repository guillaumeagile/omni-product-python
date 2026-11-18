"""La règle 6 : un effet impur dans le modèle (EI001), son remplacement dans les tests (EI002)."""

import textwrap
from pathlib import Path

import pytest

from harness.rules import effet_impur, evaluate
from harness.rules.sources import Source, collect_tests
from harness.rules.ubiquitous_language import UbiquitousLanguage
from harness.scorecard import checkout


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


# --- EI002 : le remplacement d'un effet dans les tests -----------------------------------------


def patches_of(text: str) -> list[str]:
    found = effet_impur.check_tests(source(text), UbiquitousLanguage.load())
    return [finding.effect for finding in found]


@pytest.mark.parametrize(
    ("imports", "usage", "effect"),
    [
        ("from unittest.mock import patch", "@patch('m.date')\ndef test_a(fake): ...", "patch"),
        (
            "from unittest.mock import patch",
            "def test_a():\n    with patch.object(m, 'date'): ...",
            "patch.object",
        ),
        (
            "from unittest import mock",
            "def test_a():\n    with mock.patch('m.date'): ...",
            "mock.patch",
        ),
        (
            "import unittest.mock",
            "def test_a():\n    unittest.mock.patch.dict('os.environ', {})",
            "unittest.mock.patch.dict",
        ),
        (
            "from freezegun import freeze_time",
            "@freeze_time('2026-01-01')\ndef test_a(): ...",
            "freeze_time",
        ),
        (
            "import freezegun",
            "def test_a():\n    freezegun.freeze_time('2026-01-01')",
            "freezegun.freeze_time",
        ),
        (
            "import time_machine",
            "def test_a():\n    time_machine.travel('2026-01-01')",
            "time_machine.travel",
        ),
        (
            "",
            "def test_a(monkeypatch):\n    monkeypatch.setattr('m.date', None)",
            "monkeypatch.setattr",
        ),
        ("", "def test_a(monkeypatch):\n    monkeypatch.setenv('HOME', 'x')", "monkeypatch.setenv"),
        ("", "def test_a(mocker):\n    mocker.patch('m.date')", "mocker.patch"),
        ("", "def test_a(mocker):\n    mocker.patch.object(m, 'date')", "mocker.patch.object"),
    ],
)
def test_replacing_an_effect_in_a_test_is_a_finding(imports: str, usage: str, effect: str):
    assert patches_of(f"{imports}\n\n{usage}\n") == [effect]


def test_a_fake_passed_as_parameter_is_not_a_finding():
    text = """
        from datetime import date
        from unittest.mock import MagicMock

        def test_a():
            clock = MagicMock()
            clock.today.return_value = date(2026, 11, 10)
            assert days_before_expiry(date(2026, 11, 15), clock.today()) == 5
        """

    assert patches_of(text) == []


def test_a_mocker_spy_is_not_a_patch():
    assert patches_of("def test_a(mocker):\n    mocker.MagicMock()\n") == []


def test_a_test_finding_has_its_own_code_and_names_the_fix():
    [finding] = effet_impur.check_tests(
        source("from unittest.mock import patch\n\n@patch('x')\ndef test_a(fake): ...\n"),
        UbiquitousLanguage.load(),
    )

    assert finding.code == effet_impur.CODE_TESTS == "EI002"
    assert "dans un test" in finding.message
    assert "un faux en paramètre" in finding.message


def test_every_patch_is_reported_in_line_order():
    text = """
        from unittest.mock import patch

        def test_a():
            with patch.object(m, 'a'), patch.object(m, 'b'):
                ...
        """

    found = effet_impur.check_tests(source(text), UbiquitousLanguage.load())

    assert [(f.line, f.col) for f in found] == [(5, 10), (5, 32)]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


def test_collect_tests_reads_every_file_under_tests_except_the_excluded(tmp_path: Path):
    write(tmp_path / "tests" / "test_a.py", "x = 1\n")
    write(tmp_path / "tests" / "conftest.py", "y = 2\n")
    write(tmp_path / "tests" / "harness" / "test_h.py", "z = 3\n")

    found = collect_tests(tmp_path / "tests", [tmp_path / "tests" / "harness"])

    assert [source.module for source in found] == ["tests.conftest", "tests.test_a"]


def project(tmp_path: Path, test_text: str | None) -> Path:
    src = tmp_path / "src"
    write(src / "omni_product" / "domain" / "model" / "pure.py", "def f() -> int:\n    return 1\n")
    if test_text is not None:
        write(tmp_path / "tests" / "test_pure.py", test_text)
        write(tmp_path / "tests" / "harness" / "test_h.py", test_text)
    return src


def test_the_rule_counts_the_patches_of_the_tests_with_its_findings(tmp_path: Path):
    src = project(
        tmp_path, "from unittest.mock import patch\n\n@patch('x')\ndef test_a(fake): ...\n"
    )

    [finding] = evaluate(src)[6]

    assert "tests/test_pure.py:3:2: EI002" in str(finding)


def test_the_tests_of_the_harness_are_not_read(tmp_path: Path):
    src = project(tmp_path, "def test_a(monkeypatch):\n    monkeypatch.setenv('A', 'b')\n")

    findings = [str(finding) for finding in evaluate(src)[6]]

    assert all("tests/harness" not in finding for finding in findings)
    assert len(findings) == 1


def test_a_project_without_tests_has_no_test_finding(tmp_path: Path):
    assert evaluate(project(tmp_path, None))[6] == []


def test_the_base_of_the_scorecard_brings_its_tests_along():
    with checkout("HEAD") as base_src:
        assert base_src is not None
        assert (base_src.parent / "tests").is_dir()
