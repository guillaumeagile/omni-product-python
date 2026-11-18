from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from omni_product.config import Settings
from omni_product.controller import product_controller, supplier_controller
from omni_product.infrastructure.persistence.in_memory import ProductTable, SupplierTable


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        timeout = httpx.Timeout(
            settings.external_api_read_timeout, connect=settings.external_api_connect_timeout
        )
        with httpx.Client(timeout=timeout) as http_client:
            app.state.http_client = http_client
            yield

    app = FastAPI(title="Omni Product", lifespan=lifespan)
    app.state.settings = settings
    products: ProductTable = {}
    suppliers: SupplierTable = {}
    app.state.products = products
    app.state.suppliers = suppliers

    app.include_router(product_controller.router)
    app.include_router(supplier_controller.router)
    return app


app = create_app()
