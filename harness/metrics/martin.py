"""Les métriques de Robert Martin par couche : Ca, Ce, I, A et D.

Une couche est un sous-paquet de `omni_product/` (`domain`, `infrastructure`, `dal`…) ou un module posé directement
dedans (`main`). Les liens sont les imports d'un module vers un module d'une autre couche du projet, avec leur sens.
Un import dans un bloc `if TYPE_CHECKING:` compte : une annotation est déjà une dépendance.

L'unité comptée est le module, là où Martin compte les classes : `dal/` n'a que des fonctions, et une couche sans
classe resterait muette.

- Ca (couplage afférent) : les modules d'autres couches qui importent la couche. Ils cassent quand elle change.
- Ce (couplage efférent) : les modules de la couche qui importent une autre couche. Elle casse quand l'autre change.
- I (instabilité) = Ce / (Ca + Ce), de 0 (stable : on dépend d'elle, elle ne dépend de rien) à 1 (instable).
- A (abstraction) : la part des classes abstraites de la couche (`Protocol`, `ABC`, une `@abstractmethod`).
- D (distance à la séquence principale) = |A + I - 1|. À 0, la couche est soit stable et abstraite, soit instable et
  concrète. Près de 1, elle est stable et concrète (dure à changer) ou instable et abstraite (abstraite pour rien).

Ca ne voit que les modules mesurés : une couche hors du périmètre n'apporte pas de lien afférent. Ce voit tous les
imports d'un module mesuré vers le projet, même vers une couche hors du périmètre.
"""

import ast
from collections import defaultdict
from dataclasses import dataclass

from harness.metrics.classes import top_level_classes
from harness.metrics.coupling import absolute_module
from harness.metrics.sources import SourceFile
from harness.perimetre import PACKAGE

_ABSTRACT_BASES = frozenset({"Protocol", "ABC"})


@dataclass(frozen=True)
class LayerMetrics:
    """Une couche. `instability` et `distance` sont indéfinies (None) quand la couche n'a aucun lien."""

    name: str
    modules: int
    classes: int
    abstract_classes: int
    afferent: int
    efferent: int
    instability: float | None
    abstractness: float
    distance: float | None
    depends_on: tuple[str, ...]


def measure(sources: list[SourceFile]) -> tuple[LayerMetrics, ...]:
    """Une ligne par couche présente dans les sources, dans l'ordre alphabétique."""
    targets = {source.module: _layers_imported(source) for source in sources}
    by_layer: dict[str, list[SourceFile]] = defaultdict(list)
    for source in sources:
        layer = layer_of(source.module)
        if layer is not None:
            by_layer[layer].append(source)
    return tuple(_layer(name, by_layer[name], sources, targets) for name in sorted(by_layer))


def mean_distance(layers: tuple[LayerMetrics, ...]) -> float:
    """La métrique Uncle Bob : le D moyen des couches, pondéré par leur nombre de modules.

    De 0 (chaque couche est stable et abstraite, ou instable et concrète) à 1. La pondération donne plus de poids à
    une grosse couche mal placée qu'à un module isolé. Une couche sans lien (D indéfini) n'entre pas dans la moyenne,
    et la moyenne vaut 0 quand aucune couche n'a de lien.
    """
    linked = [(layer.distance, layer.modules) for layer in layers if layer.distance is not None]
    modules = sum(weight for _, weight in linked)
    if not modules:
        return 0.0
    return round(sum(distance * weight for distance, weight in linked) / modules, 2)


def stability_violations(layers: tuple[LayerMetrics, ...]) -> tuple[tuple[str, str], ...]:
    """Les liens qui vont vers plus instable que soi : X dépend de Y alors que I(Y) > I(X).

    C'est le principe des dépendances stables. Une couche dépend de plus stable qu'elle, sinon un changement dans une
    couche instable casse une couche dont beaucoup dépendent. Un lien compte une fois par paire de couches. Un lien
    vers une couche hors du périmètre n'est pas jugé : son I est inconnu.
    """
    instability = {layer.name: layer.instability for layer in layers}
    return tuple(
        (layer.name, target)
        for layer in layers
        for target in layer.depends_on
        if (source_i := layer.instability) is not None
        and (target_i := instability.get(target)) is not None
        and target_i > source_i
    )


def layer_of(module: str) -> str | None:
    """`omni_product.domain.model.product` est dans `domain` ; le paquet racine et le reste du monde n'ont pas de couche."""
    parts = module.split(".")
    if parts[0] != PACKAGE or len(parts) < 2:
        return None
    return parts[1]


def _layer(
    name: str,
    members: list[SourceFile],
    sources: list[SourceFile],
    targets: dict[str, frozenset[str]],
) -> LayerMetrics:
    efferent = [m for m in members if targets[m.module] - {name}]
    afferent = [
        s for s in sources if layer_of(s.module) not in (name, None) and name in targets[s.module]
    ]
    classes = [cls for member in members for cls in top_level_classes(member.tree)]
    abstract = sum(1 for cls in classes if is_abstract(cls))
    abstractness = abstract / len(classes) if classes else 0.0
    links = len(afferent) + len(efferent)
    instability = len(efferent) / links if links else None
    return LayerMetrics(
        name=name,
        modules=len(members),
        classes=len(classes),
        abstract_classes=abstract,
        afferent=len(afferent),
        efferent=len(efferent),
        instability=_rounded(instability),
        abstractness=round(abstractness, 2),
        distance=None if instability is None else round(abs(abstractness + instability - 1), 2),
        depends_on=tuple(
            sorted(frozenset[str]().union(*(targets[m.module] for m in members)) - {name})
        ),
    )


def _layers_imported(source: SourceFile) -> frozenset[str]:
    """Les couches du projet que le module importe (la sienne comprise, retirée plus tard)."""
    return frozenset(
        layer
        for node in ast.walk(source.tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for target in _targets(source, node)
        if (layer := layer_of(target)) is not None
    )


def _targets(source: SourceFile, node: ast.Import | ast.ImportFrom) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    base = absolute_module(source, node)
    # `from omni_product import domain` : la couche est le nom importé, pas le paquet racine.
    return [f"{base}.{alias.name}" for alias in node.names] if base == PACKAGE else [base]


def is_abstract(cls: ast.ClassDef) -> bool:
    """Un port (`Protocol`), une `ABC`, ou une classe qui déclare une `@abstractmethod`."""
    bases = {_name(base) for base in cls.bases} | {_name(k.value) for k in cls.keywords}
    if bases & _ABSTRACT_BASES or "ABCMeta" in bases:
        return True
    return any(
        _name(decorator) == "abstractmethod"
        for node in cls.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        for decorator in node.decorator_list
    )


def _name(node: ast.expr) -> str:
    """`Protocol`, `typing.Protocol` et `Protocol[T]` se lisent tous `Protocol`."""
    if isinstance(node, ast.Subscript):
        return _name(node.value)
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.id if isinstance(node, ast.Name) else ""


def _rounded(value: float | None) -> float | None:
    return None if value is None else round(value, 2)
