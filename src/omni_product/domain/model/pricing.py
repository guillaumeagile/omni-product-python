from dataclasses import dataclass


@dataclass(frozen=True)
class Amount:
    value: float


@dataclass(frozen=True)
class TaxRate:
    value: float


# Équivalent du @Embeddable Java : valeur portée par la table de son contexte (voir dal/).
@dataclass(frozen=True)
class Price:
    base: Amount | None = None
    tax: Amount | None = None
    tax_rate: TaxRate | None = None
