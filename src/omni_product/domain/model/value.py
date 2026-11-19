"""Passage entre un Value Object et sa valeur brute, aux bords de l'application (HTTP, base)."""

from collections.abc import Callable
from typing import Protocol


class Valued[T](Protocol):
    @property
    def value(self) -> T: ...


def raw[T](valued: Valued[T] | None) -> T | None:
    return None if valued is None else valued.value


def wrap[V, R](build: Callable[[V], R], value: V | None) -> R | None:
    return None if value is None else build(value)
