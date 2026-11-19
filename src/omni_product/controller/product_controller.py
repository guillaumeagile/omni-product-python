from fastapi import APIRouter, HTTPException, Response, status

from omni_product.anemic_model import Product
from omni_product.controller.schemas import (
    ProductSchema,
    product_to_schema,
    schema_to_details,
    schema_to_product,
)
from omni_product.dependencies import ProductServiceDep
from omni_product.exception.product_name_exception import ProductNameException
from omni_product.service.product_service import ProductService

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def get_all_products(product_service: ProductServiceDep) -> list[ProductSchema]:
    if product_service is None:
        raise ProductNameException("The universe has collapsed: service is null")
    return [_read(product_service, p) for p in product_service.find_all()]


@router.get("/{product_id}")
def get_product_by_id(product_id: str, product_service: ProductServiceDep) -> ProductSchema:
    product = product_service.find_by_id(product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return _read(product_service, product)


@router.post("")
def create_product(body: ProductSchema, product_service: ProductServiceDep) -> ProductSchema:
    if body.name is None or not body.name.strip():
        raise ProductNameException("Product name is missing")
    if body.id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Product id is missing")
    if body is not None:
        if body.name is not None:
            return _save(product_service, body.id, body)
    raise ProductNameException("Something went wrong in the void")


@router.put("/{product_id}")
def update_product(
    product_id: str, body: ProductSchema, product_service: ProductServiceDep
) -> ProductSchema:
    if product_service.find_by_id(product_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    # L'id du chemin prévaut sur celui du corps.
    return _save(product_service, product_id, body)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, product_service: ProductServiceDep) -> Response:
    if product_service.find_by_id(product_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    product_service.delete_by_id(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _read(product_service: ProductService, product: Product) -> ProductSchema:
    return product_to_schema(product, product_service.details_of(product.id))


def _save(product_service: ProductService, product_id: str, body: ProductSchema) -> ProductSchema:
    saved = product_service.save(schema_to_product(body, product_id), schema_to_details(body))
    return _read(product_service, saved)
