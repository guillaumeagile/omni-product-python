from fastapi import APIRouter, HTTPException, Response, status

from omni_product.controller.schemas import (
    SupplierRequest,
    SupplierSchema,
    SupplierUpdateRequest,
    supplier_to_schema,
)
from omni_product.dependencies import SupplierServiceDep
from omni_product.domain.model import Country, Email, Phone, ProductId, Region, SupplierId

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])

type _SupplierDetails = tuple[str | None, Email | None, Phone | None, Country | None, Region | None]


def _details_of(request: SupplierUpdateRequest) -> _SupplierDetails:
    """Les coordonnées du corps de requête, en Value Objects."""
    return (
        request.name,
        Email(request.contact_email) if request.contact_email is not None else None,
        Phone(request.contact_phone) if request.contact_phone is not None else None,
        Country(request.country) if request.country is not None else None,
        Region(request.region) if request.region is not None else None,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_supplier(
    request: SupplierRequest, supplier_service: SupplierServiceDep
) -> SupplierSchema:
    supplier = supplier_service.create_supplier(SupplierId(request.id), *_details_of(request))
    return supplier_to_schema(supplier)


@router.get("/product/{product_id}")
def get_suppliers_by_product(
    product_id: str, supplier_service: SupplierServiceDep
) -> list[SupplierSchema]:
    return [
        supplier_to_schema(s)
        for s in supplier_service.get_suppliers_by_product(ProductId(product_id))
    ]


@router.get("/country/{country}")
def get_suppliers_by_country(
    country: str, supplier_service: SupplierServiceDep
) -> list[SupplierSchema]:
    return [
        supplier_to_schema(s) for s in supplier_service.get_suppliers_by_country(Country(country))
    ]


@router.get("/region/{region}")
def get_suppliers_by_region(
    region: str, supplier_service: SupplierServiceDep
) -> list[SupplierSchema]:
    return [supplier_to_schema(s) for s in supplier_service.get_suppliers_by_region(Region(region))]


@router.get("/{supplier_id}")
def get_supplier(supplier_id: str, supplier_service: SupplierServiceDep) -> SupplierSchema:
    supplier = supplier_service.get_supplier(SupplierId(supplier_id))
    if supplier is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return supplier_to_schema(supplier)


@router.get("")
def get_all_suppliers(supplier_service: SupplierServiceDep) -> list[SupplierSchema]:
    return [supplier_to_schema(s) for s in supplier_service.get_all_suppliers()]


@router.put("/{supplier_id}")
def update_supplier(
    supplier_id: str, request: SupplierUpdateRequest, supplier_service: SupplierServiceDep
) -> SupplierSchema:
    supplier = supplier_service.update_supplier(SupplierId(supplier_id), *_details_of(request))
    return supplier_to_schema(supplier)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: str, supplier_service: SupplierServiceDep) -> Response:
    supplier_service.delete_supplier(SupplierId(supplier_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
