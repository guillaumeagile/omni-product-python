"""Les identifiants des entités : un type par entité, pour ne jamais confondre deux `str`."""

from dataclasses import dataclass

from omni_product.domain.exception.invalid_value import InvalidValue


@dataclass(frozen=True)
class ProductId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvalidValue("Product id is required")


@dataclass(frozen=True)
class SupplierId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvalidValue("Supplier id is required")
