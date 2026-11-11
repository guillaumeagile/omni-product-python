"""Cohésion d'une classe : TCC et LCOM*.

Les deux partent de la même observation : quelles méthodes d'instance touchent quels attributs de `self`.
Une classe cohésive a des méthodes qui travaillent sur les mêmes données.
"""

import ast
from itertools import combinations

from harness.metrics.classes import attributes_by_method


def tcc(cls: ast.ClassDef) -> float | None:
    """Tight Class Cohesion : part des paires de méthodes qui partagent au moins un attribut (de 0 à 1, 1 est le mieux).

    Indéfinie (None) sous deux méthodes : il n'y a pas de paire à regarder.
    """
    methods = attributes_by_method(cls)
    pairs = list(combinations(methods, 2))
    if not pairs:
        return None
    return sum(1 for a, b in pairs if a & b) / len(pairs)


def lcom(cls: ast.ClassDef) -> float | None:
    """LCOM* (Henderson-Sellers), de 0 à 1 : 0 quand toutes les méthodes touchent tous les attributs, 1 quand chaque
    attribut n'est touché que par une méthode (la classe est plusieurs classes collées ensemble).

    Seuls comptent les attributs touchés par au moins une méthode d'instance. Indéfinie (None) sous deux méthodes ou
    sans attribut.
    """
    methods = attributes_by_method(cls)
    attributes: frozenset[str] = frozenset[str]().union(*methods)
    if len(methods) < 2 or not attributes:
        return None
    average_methods_per_attribute = sum(
        sum(1 for m in methods if a in m) for a in attributes
    ) / len(attributes)
    return max(0.0, (average_methods_per_attribute - len(methods)) / (1 - len(methods)))
