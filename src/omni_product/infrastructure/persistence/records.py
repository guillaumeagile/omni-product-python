"""Passages entre les records du modèle (`Slug("x")`) et les valeurs brutes de l'API (`"x"`)."""

from collections.abc import Callable
from typing import Protocol


class HasValue[T](Protocol):
    @property
    def value(self) -> T: ...


def optional[A, T](record: Callable[[A], T], value: A | None) -> T | None:
    """Le record construit depuis la valeur, ou `None` si la valeur est absente."""
    return None if value is None else record(value)


def raw[T](record: HasValue[T] | None) -> T | None:
    """La valeur brute du record, ou `None` s'il est absent."""
    return None if record is None else record.value
