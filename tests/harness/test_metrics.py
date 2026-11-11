"""Les mesures du harnais, sur de petits exemples dont on connaît la réponse."""

import textwrap
from pathlib import Path

from harness import scorecard
from harness.metrics import cohesion, complexity, coupling, style, tokens
from harness.metrics.classes import top_level_classes
from harness.metrics.report import measure
from harness.metrics.sources import SourceFile, collect


def source(text: str, module: str = "pkg.mod", *, is_package: bool = False) -> SourceFile:
    return SourceFile.from_text(module, textwrap.dedent(text), is_package=is_package)


def only_class(text: str):
    return top_level_classes(source(text).tree)[0]


def test_cyclomatic_and_cognitive_complexity_of_nested_branches():
    measured = complexity.measure(
        source(
            """
            class A:
                def f(self, x):
                    if x:
                        for i in x:
                            if i:
                                return 1
                    return 0

                def g(self):
                    return 1
            """
        )
    )

    by_name = {fn.name: fn for fn in measured}
    assert by_name["A.f"].cyclomatic == 4
    assert by_name["A.f"].cognitive == 6  # l'imbrication coûte : 1 + 2 + 3
    assert by_name["A.g"].cyclomatic == 1
    assert by_name["A.g"].cognitive == 0


def test_module_level_functions_are_measured_too():
    measured = complexity.measure(source("def f(x):\n    return 1 if x else 2\n"))

    assert [(fn.name, fn.cyclomatic) for fn in measured] == [("f", 2)]


def test_tcc_is_one_when_all_methods_share_an_attribute():
    cls = only_class(
        """
        class Counter:
            def __init__(self):
                self.n = 0
            def inc(self):
                self.n += 1
            def reset(self):
                self.n = 0
        """
    )

    assert cohesion.tcc(cls) == 1.0
    assert cohesion.lcom(cls) == 0.0


def test_tcc_and_lcom_detect_two_classes_glued_together():
    cls = only_class(
        """
        class Glued:
            def a1(self): return self.a
            def a2(self): return self.a
            def b1(self): return self.b
            def b2(self): return self.b
        """
    )

    # 6 paires de méthodes, 2 seulement partagent un attribut (a1-a2 et b1-b2)
    assert cohesion.tcc(cls) == 2 / 6
    # 2 attributs, chacun touché par 2 méthodes sur 4 : (2 - 4) / (1 - 4)
    assert cohesion.lcom(cls) == 2 / 3


def test_lcom_is_one_when_each_attribute_has_a_single_method():
    cls = only_class(
        """
        class Apart:
            def a(self): return self.x
            def b(self): return self.y
        """
    )

    assert cohesion.lcom(cls) == 1.0
    assert cohesion.tcc(cls) == 0.0


def test_cohesion_is_undefined_under_two_methods():
    cls = only_class("class Lonely:\n    def a(self):\n        return self.x\n")

    assert cohesion.tcc(cls) is None
    assert cohesion.lcom(cls) is None


def test_cohesion_ignores_constructor_static_and_class_methods_and_calls_to_own_methods():
    cls = only_class(
        """
        class C:
            def __init__(self):
                self.x = 1
                self.y = 2
            @staticmethod
            def s(): return 1
            @classmethod
            def make(cls): return cls.z
            def a(self): return self.x + self.b()
            def b(self): return self.x
        """
    )

    # a et b partagent x ; self.b() est un appel de méthode, pas un attribut
    assert cohesion.tcc(cls) == 1.0


def test_fan_out_counts_imported_and_neighbour_types_but_not_stdlib_constants_or_functions():
    sources = [
        source(
            """
            from collections.abc import Sequence
            from other import Gadget, helper, LIMIT
            import lib

            class Neighbour: ...

            class A(Neighbour):
                def f(self) -> Sequence[int]:
                    helper(LIMIT)
                    return [Gadget(), lib.Widget()]
            """
        )
    ]

    result = coupling.measure(sources)["pkg.mod.A"]

    assert result.dependencies == {"pkg.mod.Neighbour", "other.Gadget", "lib.Widget"}
    assert result.fan_out == 3


def test_cbo_adds_the_classes_that_depend_on_this_one():
    sources = [
        source("class Base: ...\n", "pkg.base"),
        source("from pkg.base import Base\n\nclass User:\n    b: Base\n", "pkg.user"),
        source("from pkg.base import Base\n\nclass Other:\n    b: Base\n", "pkg.other"),
    ]

    result = coupling.measure(sources)

    assert result["pkg.base.Base"].fan_out == 0
    assert result["pkg.base.Base"].cbo == 2
    assert result["pkg.user.User"].fan_out == 1
    assert result["pkg.user.User"].cbo == 1


def test_coupling_follows_re_exports_through_the_package_init():
    sources = [
        source("class Product: ...\n", "pkg.model.product"),
        source("from .product import Product\n", "pkg.model", is_package=True),
        source("from pkg.model import Product\n\nclass Service:\n    p: Product\n", "pkg.service"),
    ]

    result = coupling.measure(sources)

    assert result["pkg.service.Service"].dependencies == {"pkg.model.product.Product"}
    assert result["pkg.model.product.Product"].cbo == 1


def test_report_aggregates_per_class_measures():
    metrics = measure(
        [
            source(
                """
                class A:
                    def f(self, x):
                        if x:
                            return self.v
                        return 0
                    def g(self):
                        return self.v
                """
            )
        ]
    )

    assert metrics.classes == 1
    assert metrics.cyclomatic == 3
    assert metrics.max_cyclomatic == 2
    assert metrics.max_wmc == 3
    assert metrics.min_tcc == 1.0
    assert metrics.max_lcom == 0.0
    assert metrics.per_class[0].name == "pkg.mod.A"


def test_report_defaults_when_nothing_is_measurable():
    metrics = measure([])

    assert (metrics.classes, metrics.cyclomatic, metrics.min_tcc, metrics.max_lcom) == (
        0,
        0,
        1.0,
        0.0,
    )


def test_report_serialises_to_json():
    assert '"per_class": []' in measure([]).to_json()


def test_collect_derives_module_names_from_paths(tmp_path: Path):
    package = tmp_path / "pkg" / "sub"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "mod.py").write_text("class A: ...\n", encoding="utf-8")

    files = collect([tmp_path / "pkg"], tmp_path)

    assert [(f.module, f.is_package) for f in files] == [("pkg.sub", True), ("pkg.sub.mod", False)]


def test_the_real_perimeter_can_be_measured():
    root = Path(__file__).resolve().parents[2]
    metrics = measure(
        collect([root / "src/omni_product/model", root / "src/omni_product/service"], root / "src")
    )

    assert metrics.classes > 0
    assert metrics.cyclomatic >= metrics.max_cyclomatic > 0


def test_tokens_count_more_for_longer_code():
    assert 0 < tokens.count("x = 1") < tokens.count("x = 1\ny = x + 2\nz = y * 3\n")


def test_style_signals_count_state_loops_and_lambdas():
    styled = style.measure(
        [
            source(
                """
                from dataclasses import dataclass

                @dataclass(frozen=True)
                class Frozen:
                    a: int

                @dataclass
                class Loose:
                    a: int
                    b: int

                class Plain:
                    def __init__(self):
                        self.x = 0
                        self.y = 0

                    def bump(self):
                        self.x += 1

                def total(items):
                    result = 0
                    for item in items:
                        result += item
                    while result > 10:
                        result -= 1
                    return sorted(items, key=lambda i: -i)
                """
            )
        ]
    )

    assert styled.mutable_attributes == 3  # Loose.a, Loose.b, Plain.x (réassigné hors __init__)
    assert styled.assignments == 9
    assert styled.loops == 2
    assert styled.lambdas == 1


def test_report_includes_tokens_and_style():
    metrics = measure(
        [source("class A:\n    def f(self):\n        for i in []:\n            pass\n")]
    )

    assert metrics.tokens > 0
    assert metrics.loops == 1


def test_scorecard_compares_head_to_base_and_shows_direction():
    base = measure(
        [
            source(
                "class A:\n    def f(self, x):\n        if x:\n            return 1\n        return 0\n"  # noqa: E501
            )
        ]
    )
    head = measure([source("class A:\n    def f(self, x):\n        return x\n")])

    card = scorecard.render(head, base, changed_tokens=12)

    assert card.startswith(scorecard.MARKER)
    assert "| Complexité cyclomatique (total) | 2 | 1 | -1 | ✅ |" in card
    assert "🤏 Small diff" in card
    assert "`pkg.mod.A`" in card


def test_scorecard_without_base_shows_only_the_pr_values():
    card = scorecard.render(measure([source("class A:\n    pass\n")]), None)

    assert "Pas de base comparable" in card
    assert "| Classes" not in card


def test_tokens_ignore_comments_docstrings_and_formatting():
    bare = source("def f(x):\n    return x + 1\n")
    noisy = source(
        """
        def f(x):
            \"\"\"Une docstring bien longue qui ne coûte rien.\"\"\"
            # un commentaire
            return (x   +   1)
        """
    )

    assert measure([noisy]).tokens == measure([bare]).tokens


def test_collect_skips_test_files(tmp_path: Path):
    (tmp_path / "pkg" / "tests").mkdir(parents=True)
    (tmp_path / "pkg" / "a.py").write_text("x = 1\n")
    (tmp_path / "pkg" / "test_a.py").write_text("x = 1\n")
    (tmp_path / "pkg" / "tests" / "b.py").write_text("x = 1\n")

    assert [s.module for s in collect([tmp_path / "pkg"], tmp_path)] == ["pkg.a"]


def test_changed_tokens_ignore_comment_only_changes(tmp_path: Path):
    for name, text in (("base", "x = 1\n"), ("head", "# nouveau commentaire\nx = 1\n")):
        (tmp_path / name / "pkg").mkdir(parents=True)
        (tmp_path / name / "pkg" / "a.py").write_text(text)

    assert scorecard.changed_tokens(tmp_path / "base", tmp_path / "head", ["pkg"]) == 0
