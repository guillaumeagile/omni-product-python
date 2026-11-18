from fastapi import APIRouter, HTTPException, Response, status
from result import Err, Ok

from omni_product.controller.erreurs import valeur_invalide
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
    match supplier_service.create_supplier(request.id, request.name):
        case Err(erreur):
            raise valeur_invalide(erreur)
        case Ok(supplier):
            return supplier_to_schema(supplier)


@router.get("/product/{product_id}")
def get_suppliers_by_product(
    product_id: str, supplier_service: SupplierServiceDep
) -> list[SupplierSchema]:
    match supplier_service.get_suppliers_by_product(product_id):
        case Err(erreur):
            raise valeur_invalide(erreur)
        case Ok(suppliers):
            return [supplier_to_schema(s) for s in suppliers]


@router.get("/{supplier_id}")
def get_supplier(supplier_id: str, supplier_service: SupplierServiceDep) -> SupplierSchema:
    match supplier_service.get_supplier(supplier_id):
        case Err(erreur):
            raise valeur_invalide(erreur)
        case Ok(supplier) if supplier is not None:
            return supplier_to_schema(supplier)
        case Ok(_):
            raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.get("")
def get_all_suppliers(supplier_service: SupplierServiceDep) -> list[SupplierSchema]:
    return [supplier_to_schema(s) for s in supplier_service.get_all_suppliers()]


@router.put("/{supplier_id}")
def update_supplier(
    supplier_id: str, request: SupplierUpdateRequest, supplier_service: SupplierServiceDep
) -> SupplierSchema:
    match supplier_service.update_supplier(supplier_id, request.name):
        case Err(erreur):
            raise valeur_invalide(erreur)
        case Ok(supplier):
            return supplier_to_schema(supplier)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: str, supplier_service: SupplierServiceDep) -> Response:
    match supplier_service.delete_supplier(supplier_id):
        case Err(erreur):
            raise valeur_invalide(erreur)
        case Ok(_):
            return Response(status_code=status.HTTP_204_NO_CONTENT)
