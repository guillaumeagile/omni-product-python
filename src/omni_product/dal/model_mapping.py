"""Mapping du modèle de domaine vers les tables `products` et `suppliers`.

Le modèle ignore le stockage : c'est ici que SQLAlchemy se branche, de l'extérieur,
en style impératif. Le mapping s'enregistre à l'import de ce module, une fois par processus
(voir `dal/__init__.py`).

`Supplier` est mappé tel quel. `Product` ne l'est pas : sa variante (`shelf_life`) est une valeur
composée, que la table aplatit en `kind` et colonnes périssables. `ProductRecord` est la ligne de
`products`, et `product_dal` traduit `Product` et `ProductRecord`.
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table

from omni_product.dal.value_object_type import ValueObjectType
from omni_product.database import Base
from omni_product.domain.model.product import ProductId, ShelfLifeDays, Slug
from omni_product.domain.model.supplier import Country, Email, Phone, Region, Supplier, SupplierId

suppliers = Table(
    "suppliers",
    Base.metadata,
    Column("id", ValueObjectType(SupplierId, String()), primary_key=True),
    Column("name", String),
    Column("contact_email", ValueObjectType(Email, String())),
    Column("contact_phone", ValueObjectType(Phone, String())),
    Column("country", ValueObjectType(Country, String())),
    Column("region", ValueObjectType(Region, String())),
)

# Une seule table : `kind` dit la variante, les colonnes périssables sont nulles pour les autres.
products = Table(
    "products",
    Base.metadata,
    Column("id", ValueObjectType(ProductId, String()), primary_key=True),
    Column("kind", String, nullable=False),
    Column("name", String, nullable=False),
    Column("slug", ValueObjectType(Slug, String()), unique=True, nullable=False),
    Column("supplier_id", ValueObjectType(SupplierId, String()), ForeignKey("suppliers.id")),
    Column("expiration_date", Date),
    Column("shelf_life_days", ValueObjectType(ShelfLifeDays, Integer())),
)


@dataclass(eq=False)
class ProductRecord:
    """Une ligne de `products`, à plat."""

    id: ProductId
    kind: str
    name: str
    slug: Slug
    supplier_id: SupplierId | None
    expiration_date: date | None
    shelf_life_days: ShelfLifeDays | None


Base.registry.map_imperatively(Supplier, suppliers)
Base.registry.map_imperatively(ProductRecord, products)
