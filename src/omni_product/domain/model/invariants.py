from collections.abc import Callable, Iterable
from typing import Any

from result import Err, Ok, Result

from omni_product.domain.model.errors import InvalidValueError


def require_text(owner: type, value: str) -> Result[str, InvalidValueError]:
    if not value.strip():
        return Err(InvalidValueError(f"{owner.__name__} ne peut pas être vide"))
    return Ok(value)


def require_at_least_zero[N: float](owner: type, value: N) -> Result[N, InvalidValueError]:
    if value < 0:
        return Err(InvalidValueError(f"{owner.__name__} ne peut pas être négatif"))
    return Ok(value)


def require_rate(owner: type, value: float) -> Result[float, InvalidValueError]:
    if not 0 <= value <= 1:
        return Err(InvalidValueError(f"{owner.__name__} doit être entre 0 et 1"))
    return Ok(value)


def optionnel[A, T, E](of: Callable[[A], Result[T, E]], value: A | None) -> Result[T | None, E]:
    """La valeur validée par `of`, ou `None` si la valeur est absente."""
    if value is None:
        return Ok(None)
    return of(value)


def premiere_erreur(
    resultats: Iterable[Result[Any, InvalidValueError]],
) -> InvalidValueError | None:
    """Le premier échec de la liste, ou `None` si toutes les valeurs sont valides."""
    for resultat in resultats:
        match resultat:
            case Err(erreur):
                return erreur
            case Ok(_):
                continue
    return None
