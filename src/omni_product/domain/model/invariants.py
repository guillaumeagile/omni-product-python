from collections.abc import Callable

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
