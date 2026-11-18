from typing import Annotated

import httpx
from fastapi import Depends, Request

from omni_product.config import Settings
from omni_product.domain.port.transport_carbon_port import TransportCarbonPort
from omni_product.infrastructure.adapter.impact_co2_api_client import ImpactCo2ApiClient
from omni_product.infrastructure.adapter.impact_co2_transport_adapter import (
    ImpactCo2TransportAdapter,
)
from omni_product.infrastructure.persistence.in_memory import (
    InMemoryProductRepository,
    InMemorySupplierRepository,
    ProductTable,
    SupplierTable,
)
from omni_product.service.product_service import ProductService
from omni_product.service.product_transport_service import ProductTransportService
from omni_product.service.supplier_service import SupplierService


def get_product_repository(request: Request) -> InMemoryProductRepository:
    products: ProductTable = request.app.state.products
    return InMemoryProductRepository(products)


def get_supplier_repository(request: Request) -> InMemorySupplierRepository:
    suppliers: SupplierTable = request.app.state.suppliers
    products: ProductTable = request.app.state.products
    return InMemorySupplierRepository(suppliers, products)


ProductRepositoryDep = Annotated[InMemoryProductRepository, Depends(get_product_repository)]
SupplierRepositoryDep = Annotated[InMemorySupplierRepository, Depends(get_supplier_repository)]


def get_product_service(products: ProductRepositoryDep) -> ProductService:
    return ProductService(products)


def get_supplier_service(
    suppliers: SupplierRepositoryDep, products: ProductRepositoryDep
) -> SupplierService:
    return SupplierService(suppliers, products)


def get_transport_carbon_port(request: Request) -> TransportCarbonPort:
    settings: Settings = request.app.state.settings
    http_client: httpx.Client = request.app.state.http_client
    return ImpactCo2TransportAdapter(ImpactCo2ApiClient(http_client, settings.impactco2_base_url))


def get_product_transport_service(
    port: Annotated[TransportCarbonPort, Depends(get_transport_carbon_port)],
) -> ProductTransportService:
    return ProductTransportService(port)


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
SupplierServiceDep = Annotated[SupplierService, Depends(get_supplier_service)]
