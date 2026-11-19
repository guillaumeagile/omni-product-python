"""Mapping du modèle de domaine vers les tables `products` et `suppliers`.

Le modèle ignore le stockage : c'est ici que SQLAlchemy se branche, de l'extérieur,
en style impératif. Le mapping s'enregistre à l'import de ce module, une fois par processus
(voir `dal/__init__.py`).
"""

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table

from omni_product.database import Base
from omni_product.domain.model.product import NonExpiringProduct, PerishableProduct, Product
from omni_product.domain.model.supplier import Supplier

suppliers = Table(
    "suppliers",
    Base.metadata,
    Column("id", String, primary_key=True),
    Column("name", String),
    Column("contact_email", String),
    Column("contact_phone", String),
    Column("country", String),
    Column("region", String),
)

# Héritage mono-table : toutes les variantes partagent la table `products`, discriminée par `kind`.
products = Table(
    "products",
    Base.metadata,
    Column("id", String, primary_key=True),
    Column("kind", String, nullable=False),
    Column("name", String, nullable=False),
    Column("slug", String, unique=True, nullable=False),
    Column("supplier_id", String, ForeignKey("suppliers.id")),
    Column("expiration_date", Date),
    Column("shelf_life_days", Integer),
)

Base.registry.map_imperatively(Supplier, suppliers)
# Les colonnes périssables ne sont mappées que sur PerishableProduct. `with_polymorphic` les charge
# dans la même requête que `select(Product)`, sans une requête de plus par produit périssable.
Base.registry.map_imperatively(
    Product,
    products,
    polymorphic_on=products.c.kind,
    polymorphic_identity="standard",
    with_polymorphic="*",
    exclude_properties=["expiration_date", "shelf_life_days"],
)
Base.registry.map_imperatively(
    PerishableProduct,
    inherits=Product,
    polymorphic_identity="perishable",
    properties={
        "expiration_date": products.c.expiration_date,
        "shelf_life_days": products.c.shelf_life_days,
    },
)
Base.registry.map_imperatively(
    NonExpiringProduct,
    inherits=Product,
    polymorphic_identity="non_expiring",
)
