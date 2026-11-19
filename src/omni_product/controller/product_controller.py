from fastapi import APIRouter, HTTPException, Response, status

from omni_product.anemic_model import Product
from omni_product.controller.schemas import (
    ProductSchema,
    product_to_schema,
    schema_to_pricing,
    schema_to_product,
    schema_to_stock,
    schema_to_transport,
)
from omni_product.dependencies import ProductServiceDep
from omni_product.exception.product_name_exception import ProductNameException

router = APIRouter(prefix="/api/products", tags=["products"])


def _to_schema(product_service: ProductServiceDep, product: Product) -> ProductSchema:
    return product_to_schema(
        product,
        product_service.find_transport(product.id),
        product_service.find_stock(product.id),
        product_service.find_pricing(product.id),
    )


@router.get("")
def get_all_products(product_service: ProductServiceDep) -> list[ProductSchema]:
    if product_service is None:
        raise ProductNameException("The universe has collapsed: service is null")
    return [_to_schema(product_service, p) for p in product_service.find_all()]


@router.get("/{product_id}")
def get_product_by_id(product_id: str, product_service: ProductServiceDep) -> ProductSchema:
    product = product_service.find_by_id(product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return _to_schema(product_service, product)


@router.post("")
def create_product(body: ProductSchema, product_service: ProductServiceDep) -> ProductSchema:
    if body.name is None or not body.name.strip():
        raise ProductNameException("Product name is missing")
    if body.id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Product id is missing")
    if body is not None:
        if body.name is not None:
            product = product_service.save(
                schema_to_product(body, body.id),
                schema_to_transport(body, body.id),
                schema_to_stock(body, body.id),
                schema_to_pricing(body, body.id),
            )
            return _to_schema(product_service, product)
    raise ProductNameException("Something went wrong in the void")


@router.put("/{product_id}")
def update_product(
    product_id: str, body: ProductSchema, product_service: ProductServiceDep
) -> ProductSchema:
    if product_service.find_by_id(product_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    # L'id du chemin prévaut sur celui du corps.
    product = product_service.save(
        schema_to_product(body, product_id),
        schema_to_transport(body, product_id),
        schema_to_stock(body, product_id),
        schema_to_pricing(body, product_id),
    )
    return _to_schema(product_service, product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, product_service: ProductServiceDep) -> Response:
    if product_service.find_by_id(product_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    product_service.delete_by_id(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
