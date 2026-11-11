"""Le rapport de mesures : une ligne par classe, et les agrégats que l'arbitre comparera d'une PR à l'autre."""

import ast
import json
from dataclasses import asdict, dataclass

from harness.metrics import cohesion, complexity, coupling
from harness.metrics.classes import top_level_classes
from harness.metrics.sources import SourceFile


@dataclass(frozen=True)
class ClassMetrics:
    name: str
    wmc: int
    cognitive: int
    tcc: float | None
    lcom: float | None
    fan_out: int
    cbo: int
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class Metrics:
    """Les agrégats. Le `min_tcc` vaut 1 et le `max_lcom` 0 quand aucune classe n'a de cohésion mesurable."""

    classes: int
    cyclomatic: int
    max_cyclomatic: int
    max_wmc: int
    cognitive: int
    max_cognitive: int
    min_tcc: float
    max_lcom: float
    fan_out: int
    max_fan_out: int
    cbo: int
    max_cbo: int
    per_class: tuple[ClassMetrics, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


def measure(sources: list[SourceFile]) -> Metrics:
    couplings = coupling.measure(sources)
    functions = {source.module: complexity.measure(source) for source in sources}
    per_class = tuple(
        _class_metrics(source, cls, functions[source.module], couplings)
        for source in sources
        for cls in top_level_classes(source.tree)
    )
    every_function = [fn for measured in functions.values() for fn in measured]
    tccs = [m.tcc for m in per_class if m.tcc is not None]
    lcoms = [m.lcom for m in per_class if m.lcom is not None]
    return Metrics(
        classes=len(per_class),
        cyclomatic=sum(fn.cyclomatic for fn in every_function),
        max_cyclomatic=max((fn.cyclomatic for fn in every_function), default=0),
        max_wmc=max((m.wmc for m in per_class), default=0),
        cognitive=sum(fn.cognitive for fn in every_function),
        max_cognitive=max((fn.cognitive for fn in every_function), default=0),
        min_tcc=min(tccs, default=1.0),
        max_lcom=max(lcoms, default=0.0),
        fan_out=sum(m.fan_out for m in per_class),
        max_fan_out=max((m.fan_out for m in per_class), default=0),
        cbo=sum(m.cbo for m in per_class),
        max_cbo=max((m.cbo for m in per_class), default=0),
        per_class=per_class,
    )


def _class_metrics(
    source: SourceFile,
    cls: ast.ClassDef,
    functions: list[complexity.FunctionComplexity],
    couplings: dict[str, coupling.Coupling],
) -> ClassMetrics:
    own = [fn for fn in functions if fn.name.startswith(f"{cls.name}.")]
    link = couplings[f"{source.module}.{cls.name}"]
    return ClassMetrics(
        name=f"{source.module}.{cls.name}",
        wmc=sum(fn.cyclomatic for fn in own),
        cognitive=sum(fn.cognitive for fn in own),
        tcc=_rounded(cohesion.tcc(cls)),
        lcom=_rounded(cohesion.lcom(cls)),
        fan_out=link.fan_out,
        cbo=link.cbo,
        dependencies=tuple(sorted(link.dependencies)),
    )


def _rounded(value: float | None) -> float | None:
    return None if value is None else round(value, 2)
