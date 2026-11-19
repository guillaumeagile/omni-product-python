"""Types de colonne : un Value Object est stocké comme sa valeur brute, relu comme Value Object."""

from typing import Any

from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator, TypeEngine


def vo_type(vo: type[Any], impl: type[TypeEngine[Any]]) -> TypeDecorator[Any]:
    class _ValueObjectType(TypeDecorator[Any]):
        cache_ok = True

        def process_bind_param(self, value: Any, dialect: Dialect) -> Any:
            return None if value is None else value.value

        def process_result_value(self, value: Any, dialect: Dialect) -> Any:
            return None if value is None else vo(value)

    _ValueObjectType.impl = impl
    return _ValueObjectType()
