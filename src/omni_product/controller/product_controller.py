from fastapi import APIRouter, HTTPException, Response, status
from result import Err, Ok

from omni_product.controller.erreurs import valeur_invalide
from omni_product.controller.schemas import ProductSchema, product_to_schema, schema_to_product
from omni_product.dependencies import ProductServiceDep
from omni_product.service.product_service import ProductService

FAILED_DEPENDENCY = 424

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def get_all_products(product_service: ProductServiceDep) -> list[ProductSchema]:
    return [product_to_schema(p) for p in product_service.find_all()]


@router.get("/{product_id}")
def get_product_by_id(product_id: str, product_service: ProductServiceDep) -> ProductSchema:
    match product_service.find_by_id(product_id):
        case Err(erreur):
            raise valeur_invalide(erreur)
        case Ok(product) if product is not None:
            return product_to_schema(product)
        case Ok(_):
            raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.post("")
def create_product(body: ProductSchema, product_service: ProductServiceDep) -> ProductSchema:
    if body.name is None or not body.name.strip():
        # Le statut 424 est celui du contrat de l'API pour un nom absent à la création.
        raise HTTPException(FAILED_DEPENDENCY, "Product name is missing")
    if body.id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Product id is missing")
    return _sauver(body, body.id, product_service)


@router.put("/{product_id}")
def update_product(
    product_id: str, body: ProductSchema, product_service: ProductServiceDep
) -> ProductSchema:
    match product_service.find_by_id(product_id):
        case Err(erreur):
            raise valeur_invalide(erreur)
        case Ok(None):
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        case Ok(_):
            # L'id du chemin prévaut sur celui du corps.
            return _sauver(body, product_id, product_service)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, product_service: ProductServiceDep) -> Response:
    match product_service.find_by_id(product_id):
        case Err(erreur):
            raise valeur_invalide(erreur)
        case Ok(None):
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        case Ok(_):
            match product_service.delete_by_id(product_id):
                case Err(erreur):
                    raise valeur_invalide(erreur)
                case Ok(_):
                    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _sauver(body: ProductSchema, product_id: str, product_service: ProductService) -> ProductSchema:
    match schema_to_product(body, product_id):
        case Err(erreur):
            raise valeur_invalide(erreur)
        case Ok(sheet):
            return product_to_schema(product_service.save(sheet))
