"""Le périmètre du harnais : `omni_product/`, sauf les couches externes et la plomberie."""

from pathlib import Path

from harness.perimetre import HORS_PERIMETRE, description, dossiers_exclus
from harness.rules.sources import collect


def _write(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("class A: ...\n", encoding="utf-8")


def test_controller_service_and_dal_are_out_of_the_perimeter(tmp_path: Path):
    src = tmp_path / "src"
    for name in ("domain/model/product.py", "infrastructure/x.py", "main.py", "dal/rows.py"):
        _write(src / "omni_product" / name)
    for name in HORS_PERIMETRE:
        _write(src / "omni_product" / (name if name.endswith(".py") else f"{name}/module.py"))

    modules = [s.module for s in collect([src / "omni_product"], src, dossiers_exclus(src))]

    assert modules == [
        "omni_product.domain.model.product",
        "omni_product.infrastructure.x",
        "omni_product.main",
    ]


def test_without_exclusions_every_module_is_collected(tmp_path: Path):
    src = tmp_path / "src"
    _write(src / "omni_product" / "controller" / "module.py")

    assert [s.module for s in collect([src / "omni_product"], src)] == [
        "omni_product.controller.module"
    ]


def test_the_real_perimeter_excludes_the_outer_layers():
    root = Path(__file__).resolve().parents[2]
    modules = [
        s.module
        for s in collect([root / "src/omni_product"], root / "src", dossiers_exclus(root / "src"))
    ]

    assert modules
    assert not any(
        len(parts := module.split(".")) > 1 and parts[1] in HORS_PERIMETRE for module in modules
    )


def test_the_description_lists_every_excluded_entry():
    text = description()

    assert text.startswith("`omni_product/`, hors ")
    assert all(name in text for name in HORS_PERIMETRE)
