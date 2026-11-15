from omni_product.anemic_model.errors import InvalidValueError


def require_text(owner: object, value: str) -> None:
    if not value.strip():
        raise InvalidValueError(f"{type(owner).__name__} ne peut pas être vide")


def require_at_least_zero(owner: object, value: float) -> None:
    if value < 0:
        raise InvalidValueError(f"{type(owner).__name__} ne peut pas être négatif")


def require_rate(owner: object, value: float) -> None:
    if not 0 <= value <= 1:
        raise InvalidValueError(f"{type(owner).__name__} doit être entre 0 et 1")
