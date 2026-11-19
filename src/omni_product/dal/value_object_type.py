"""Colonne d'un Value Object à un champ : la valeur brute en base, le Value Object en mémoire.

Un seul `TypeDecorator` sert tous les Value Objects `value` du modèle (`ProductId`, `Slug`,
`Amount`...). Le modèle ne sait rien de cette traduction : elle vit ici, avec le stockage.
"""

from collections.abc import Callable
from typing import Protocol

from sqlalchemy import Dialect, String
from sqlalchemy.types import TypeDecorator, TypeEngine

type Raw = str | int | float
type Column = TypeEngine[str] | TypeEngine[int] | TypeEngine[float]


class SingleValue(Protocol):
    """Un Value Object à un champ `value`."""

    @property
    def value(self) -> Raw: ...


class ValueObjectType[V: SingleValue](TypeDecorator[V]):
    """Stocke `V.value` dans la colonne `inner` et reconstruit `V` à la lecture."""

    impl = String
    cache_ok = True

    def __init__(self, factory: Callable[..., V], inner: Column) -> None:
        super().__init__()
        self.factory = factory
        self.inner = inner
        self.impl = inner

    def process_bind_param(self, value: V | None, dialect: Dialect) -> Raw | None:
        return value.value if value is not None else None

    def process_result_value(self, value: Raw | None, dialect: Dialect) -> V | None:
        return self.factory(value) if value is not None else None
