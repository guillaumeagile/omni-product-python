from typing import Any

from sqlalchemy import Dialect, Engine, String, TypeDecorator, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeEngine

from omni_product.config import Settings


class Base(DeclarativeBase):
    pass


class _RecordColumn(TypeDecorator[Any]):
    """Stocke le champ `value` d'un record (dataclass frozen à un seul champ) et rend le record."""

    cache_ok = True
    impl = String

    def __init__(self, record: type[Any], impl: type[TypeEngine[Any]]) -> None:
        super().__init__()
        self.impl = impl()
        self.record = record

    def process_bind_param(self, value: Any, dialect: Dialect) -> Any:
        return None if value is None else value.value

    def process_result_value(self, value: Any, dialect: Dialect) -> Any:
        return None if value is None else self.record(value)


def record_column(record: type[Any], impl: type[TypeEngine[Any]] = String) -> TypeDecorator[Any]:
    """Une colonne dont la valeur Python est un record : `Slug("x")` est stocké comme `"x"`."""
    return _RecordColumn(record, impl)


def create_db_engine(settings: Settings) -> Engine:
    if settings.database_url.endswith(":memory:"):
        # Une base en mémoire n'existe que par sa connexion : on la partage entre les threads.
        return create_engine(
            settings.database_url,
            echo=settings.show_sql,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(settings.database_url, echo=settings.show_sql)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)
