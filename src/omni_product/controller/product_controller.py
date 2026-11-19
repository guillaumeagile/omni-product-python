from fastapi import APIRouter, HTTPException, Response, status

from omni_product.anemic_model import (
    Product,
    ProductPricing,
    ProductStorage,
    ProductSupply,
    ProductTransport,
)
from omni_product.controller.schemas import (
    ProductSchema,
    product_to_schema,
    schema_to_contexts,
    schema_to_product,
)
from omni_product.dependencies import ProductServiceDep
from omni_product.exception.product_name_exception import ProductNameException
from omni_product.service.product_service import ProductService

router = APIRouter(prefix="/api/products", tags=["products"])


def _to_schema(product: Product, product_service: ProductService) -> ProductSchema:
    """Va chercher ce que chaque contexte sait du produit, puis assemble la réponse."""
    return product_to_schema(
        product,
        pricing=product_service.find_context(ProductPricing, product.id),
        storage=product_service.find_context(ProductStorage, product.id),
        transport=product_service.find_context(ProductTransport, product.id),
        supply=product_service.find_context(ProductSupply, product.id),
    )


def _save(body: ProductSchema, product_id: str, product_service: ProductService) -> ProductSchema:
    saved = product_service.save_with_contexts(
        schema_to_product(body, product_id), schema_to_contexts(body, product_id)
    )
    return _to_schema(saved, product_service)


@router.get("")
def get_all_products(product_service: ProductServiceDep) -> list[ProductSchema]:
    if product_service is None:
        raise ProductNameException("The universe has collapsed: service is null")
    return [_to_schema(product, product_service) for product in product_service.find_all()]


@router.get("/{product_id}")
def get_product_by_id(product_id: str, product_service: ProductServiceDep) -> ProductSchema:
    product = product_service.find_by_id(product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return _to_schema(product, product_service)


@router.post("")
def create_product(body: ProductSchema, product_service: ProductServiceDep) -> ProductSchema:
    if body.name is None or not body.name.strip():
        raise ProductNameException("Product name is missing")
    if body.id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Product id is missing")
    if body is not None:
        if body.name is not None:
            return _save(body, body.id, product_service)
    raise ProductNameException("Something went wrong in the void")


@router.put("/{product_id}")
def update_product(
    product_id: str, body: ProductSchema, product_service: ProductServiceDep
) -> ProductSchema:
    if product_service.find_by_id(product_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    # L'id du chemin prévaut sur celui du corps.
    return _save(body, product_id, product_service)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, product_service: ProductServiceDep) -> Response:
    if product_service.find_by_id(product_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    product_service.delete_by_id(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
