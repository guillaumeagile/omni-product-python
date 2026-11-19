from dataclasses import dataclass, field

from omni_product.domain.model.product_values import (
    Amount,
    Discount,
    DiscountId,
    ExpirationDate,
    ImageDetail,
    ImageKey,
    ImageRowId,
    Kilos,
    ProductId,
    ProductName,
    Quantity,
    Region,
    RegionRowId,
    ShelfLifeDays,
    Siren,
    Slug,
    Stock,
    SupplierId,
    SupplierName,
    TaxRate,
    TvaId,
    Volume,
    WarehouseLocation,
)

# Modèle pur, sans import de base de données. Le mapping vers les tables est dans `dal/mapping.py`.


# Valeurs rangées dans la table de leur contexte.
@dataclass(frozen=True)
class Price:
    base: Amount | None = None
    tax: Amount | None = None
    tax_rate: TaxRate | None = None


@dataclass(frozen=True)
class Warehouse:
    location: WarehouseLocation | None = None


@dataclass(frozen=True)
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: SupplierName | None = None
    siren: Siren | None = None
    tva_id: TvaId | None = None


@dataclass(eq=False)
class Product:
    """Entité du contexte Catalog. Les autres contextes sont des lignes liées par `product_id`."""

    id: ProductId
    name: ProductName | None
    slug: Slug | None
    images: dict[ImageKey, ImageDetail | None] = field(
        default_factory=dict[ImageKey, ImageDetail | None]
    )

    def is_perishable(self) -> bool:
        # La classe de base connaît sa sous-classe : une branche de plus à chaque nouveau type.
        return isinstance(self, PerishableProduct)


@dataclass(eq=False)
class PerishableProduct(Product):
    """Produit périssable."""

    expiration_date: ExpirationDate | None = None
    shelf_life_days: ShelfLifeDays | None = None


@dataclass(eq=False)
class NonExpiringProduct(Product):
    """Produit sans date limite. Aucun champ propre : la classe ne sert qu'à porter un type."""


@dataclass(eq=False)
class ProductPricing:
    """Contexte Pricing : son identité est celle du produit."""

    id: ProductId
    price: Price | None = None


@dataclass(eq=False)
class ProductDiscount:
    id: DiscountId | None
    product_id: ProductId
    discount: Discount


@dataclass(eq=False)
class ProductImage:
    id: ImageRowId | None
    product_id: ProductId
    image_key: ImageKey
    image_detail: ImageDetail | None = None


@dataclass(eq=False)
class ProductStorage:
    """Contexte Storage : son identité est celle du produit."""

    id: ProductId
    quantity: Quantity | None = None
    stock: Stock | None = None
    warehouse: Warehouse | None = None


@dataclass(eq=False)
class ProductTransport:
    """Contexte Transport : son identité est celle du produit."""

    id: ProductId
    kilos: Kilos | None = None
    volume: Volume | None = None


@dataclass(eq=False)
class ProductSourcing:
    """Fournisseur principal d'un produit : son identité est celle du produit."""

    id: ProductId
    supplier_id: SupplierId | None = None


@dataclass(eq=False)
class ProductSupplierRegion:
    id: RegionRowId | None
    product_id: ProductId
    region: Region
    supplier: RegionSupplier
