from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from omni_product import model  # noqa: F401  # pyright: ignore[reportUnusedImport]
from omni_product.config import Settings
from omni_product.controller import product_controller, supplier_controller
from omni_product.database import Base, create_db_engine, create_session_factory
from omni_product.exception.product_name_exception import ProductNameException

FAILED_DEPENDENCY = 424


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = create_db_engine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        Base.metadata.create_all(engine)  # ddl-auto: create-drop
        timeout = httpx.Timeout(
            settings.external_api_read_timeout, connect=settings.external_api_connect_timeout
        )
        with httpx.Client(timeout=timeout) as http_client:
            app.state.http_client = http_client
            yield
        Base.metadata.drop_all(engine)
        engine.dispose()

    app = FastAPI(title="Omni Product", lifespan=lifespan)
    app.state.settings = settings
    app.state.session_factory = create_session_factory(engine)
    app.state.engine = engine

    @app.exception_handler(ProductNameException)
    def product_name_handler(_: Request, exc: ProductNameException) -> JSONResponse:  # pyright: ignore[reportUnusedFunction]
        return JSONResponse({"detail": str(exc)}, status_code=FAILED_DEPENDENCY)

    app.include_router(product_controller.router)
    app.include_router(supplier_controller.router)
    return app


app = create_app()
