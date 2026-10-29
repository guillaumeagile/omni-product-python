from fastapi import APIRouter, HTTPException, Response, status

from omni_product.controller.schemas import (
    SupplierRequest,
    SupplierSchema,
    SupplierUpdateRequest,
    supplier_to_schema,
)
from omni_product.dependencies import SupplierServiceDep

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_supplier(
    request: SupplierRequest, supplier_service: SupplierServiceDep
) -> SupplierSchema:
    supplier = supplier_service.create_supplier(
        request.id,
        request.name,
        request.contact_email,
        request.contact_phone,
        request.country,
        request.region,
    )
    return supplier_to_schema(supplier)


@router.get("/product/{product_id}")
def get_suppliers_by_product(
    product_id: str, supplier_service: SupplierServiceDep
) -> list[SupplierSchema]:
    return [supplier_to_schema(s) for s in supplier_service.get_suppliers_by_product(product_id)]


@router.get("/country/{country}")
def get_suppliers_by_country(
    country: str, supplier_service: SupplierServiceDep
) -> list[SupplierSchema]:
    return [supplier_to_schema(s) for s in supplier_service.get_suppliers_by_country(country)]


@router.get("/region/{region}")
def get_suppliers_by_region(
    region: str, supplier_service: SupplierServiceDep
) -> list[SupplierSchema]:
    return [supplier_to_schema(s) for s in supplier_service.get_suppliers_by_region(region)]


@router.get("/{supplier_id}")
def get_supplier(supplier_id: str, supplier_service: SupplierServiceDep) -> SupplierSchema:
    supplier = supplier_service.get_supplier(supplier_id)
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
    supplier = supplier_service.update_supplier(
        supplier_id,
        request.name,
        request.contact_email,
        request.contact_phone,
        request.country,
        request.region,
    )
    return supplier_to_schema(supplier)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: str, supplier_service: SupplierServiceDep) -> Response:
    supplier_service.delete_supplier(supplier_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
