from fastapi import APIRouter, HTTPException, Response, status

from omni_product.controller.schemas import ProductSchema, schema_to_sheet, sheet_to_schema
from omni_product.dependencies import ProductServiceDep
from omni_product.exception.product_name_exception import ProductNameException

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def get_all_products(product_service: ProductServiceDep) -> list[ProductSchema]:
    if product_service is None:
        raise ProductNameException("The universe has collapsed: service is null")
    return [sheet_to_schema(sheet) for sheet in product_service.find_all_sheets()]


@router.get("/{product_id}")
def get_product_by_id(product_id: str, product_service: ProductServiceDep) -> ProductSchema:
    sheet = product_service.find_sheet(product_id)
    if sheet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return sheet_to_schema(sheet)


@router.post("")
def create_product(body: ProductSchema, product_service: ProductServiceDep) -> ProductSchema:
    if body.name is None or not body.name.strip():
        raise ProductNameException("Product name is missing")
    if body.id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Product id is missing")
    if body is not None:
        if body.name is not None:
            return sheet_to_schema(product_service.save_sheet(schema_to_sheet(body, body.id)))
    raise ProductNameException("Something went wrong in the void")


@router.put("/{product_id}")
def update_product(
    product_id: str, body: ProductSchema, product_service: ProductServiceDep
) -> ProductSchema:
    if product_service.find_by_id(product_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    # L'id du chemin prévaut sur celui du corps.
    return sheet_to_schema(product_service.save_sheet(schema_to_sheet(body, product_id)))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, product_service: ProductServiceDep) -> Response:
    if product_service.find_by_id(product_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    product_service.delete_by_id(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
