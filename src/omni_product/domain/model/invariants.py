from collections.abc import Callable, Iterable
from typing import Any

from result import Err, Ok, Result

from omni_product.domain.model.errors import InvalidValueError


def require_text[E: InvalidValueError](
    owner: type, value: str, erreur: Callable[[str], E]
) -> Result[str, E]:
    if not value.strip():
        return Err(erreur(f"{owner.__name__} ne peut pas être vide"))
    return Ok(value)


def require_at_least_zero[N: float, E: InvalidValueError](
    owner: type, value: N, erreur: Callable[[str], E]
) -> Result[N, E]:
    if value < 0:
        return Err(erreur(f"{owner.__name__} ne peut pas être négatif"))
    return Ok(value)


def require_rate[E: InvalidValueError](
    owner: type, value: float, erreur: Callable[[str], E]
) -> Result[float, E]:
    if not 0 <= value <= 1:
        return Err(erreur(f"{owner.__name__} doit être entre 0 et 1"))
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
