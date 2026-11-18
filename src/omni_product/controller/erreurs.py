from fastapi import HTTPException, status

from omni_product.domain.model.errors import InvalidValueError


def valeur_invalide(erreur: InvalidValueError) -> HTTPException:
    """La réponse 422 d'une valeur invalide, avec le message du domaine."""
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(erreur))
