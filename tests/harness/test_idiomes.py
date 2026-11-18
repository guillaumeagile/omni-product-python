"""La règle 8 : ruff lit les idiomes, sur de petits fichiers dont on connaît la réponse."""

import textwrap
from pathlib import Path

from harness.rules import idiomes
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage


def check_text(tmp_path: Path, text: str) -> list[idiomes.Finding]:
    path = tmp_path / "sample.py"
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    source = Source.from_text("sample", path.read_text(encoding="utf-8"), path=str(path))
    return idiomes.check(source, UbiquitousLanguage.load())


def test_a_loop_that_fills_a_list_is_a_finding(tmp_path: Path):
    findings = check_text(
        tmp_path,
        """
        def doubles(items):
            result = []
            for item in items:
                result.append(item * 2)
            return result
        """,
    )
    assert [finding.code for finding in findings] == ["PERF401"]
    # Le texte commence par une ligne vide : la boucle est en ligne 4, son `append` en ligne 5.
    assert findings[0].line == 5


def test_a_comprehension_is_not_a_finding(tmp_path: Path):
    findings = check_text(
        tmp_path,
        """
        def doubles(items):
            return [item * 2 for item in items]
        """,
    )
    assert findings == []


def test_a_chain_of_if_on_the_same_value_is_a_finding(tmp_path: Path):
    findings = check_text(
        tmp_path,
        """
        def label(code):
            if code == 1:
                return "a"
            elif code == 2:
                return "b"
            elif code == 3:
                return "c"
            return "?"
        """,
    )
    assert "SIM116" in [finding.code for finding in findings]


def test_a_finding_is_printed_like_ruff(tmp_path: Path):
    findings = check_text(
        tmp_path,
        """
        def doubles(items):
            result = []
            for item in items:
                result.append(item * 2)
            return result
        """,
    )
    assert str(findings[0]).endswith(": PERF401 " + findings[0].message)
    assert str(findings[0]).startswith(str(tmp_path / "sample.py") + ":5:9: PERF401 ")
