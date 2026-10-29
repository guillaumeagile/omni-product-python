from collections.abc import Iterator
from typing import Annotated

import httpx
from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from omni_product.config import Settings
from omni_product.domain.port.transport_carbon_port import TransportCarbonPort
from omni_product.infrastructure.adapter.impact_co2_api_client import ImpactCo2ApiClient
from omni_product.infrastructure.adapter.impact_co2_transport_adapter import (
    ImpactCo2TransportAdapter,
)
from omni_product.repository.product_repository import ProductRepository
from omni_product.repository.supplier_repository import SupplierRepository
from omni_product.service.product_service import ProductService
from omni_product.service.product_transport_service import ProductTransportService
from omni_product.service.supplier_service import SupplierService


def get_session(request: Request) -> Iterator[Session]:
    session_factory: sessionmaker[Session] = request.app.state.session_factory
    with session_factory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_product_repository(session: SessionDep) -> ProductRepository:
    return ProductRepository(session)


def get_supplier_repository(session: SessionDep) -> SupplierRepository:
    return SupplierRepository(session)


ProductRepositoryDep = Annotated[ProductRepository, Depends(get_product_repository)]
SupplierRepositoryDep = Annotated[SupplierRepository, Depends(get_supplier_repository)]


def get_product_service(product_repository: ProductRepositoryDep) -> ProductService:
    return ProductService(product_repository)


def get_supplier_service(
    supplier_repository: SupplierRepositoryDep, product_repository: ProductRepositoryDep
) -> SupplierService:
    return SupplierService(supplier_repository, product_repository)


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
