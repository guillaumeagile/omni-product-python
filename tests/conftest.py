from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from omni_product.config import Settings
from omni_product.main import create_app


@pytest.fixture
def app() -> Iterator[FastAPI]:
    """Une application et une base en mémoire neuves par test (`create_all` / `drop_all`)."""
    application = create_app(Settings(show_sql=False))
    with TestClient(application):  # déclenche le lifespan
        yield application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def session(app: FastAPI) -> Iterator[Session]:
    with app.state.session_factory() as db_session:
        yield db_session
