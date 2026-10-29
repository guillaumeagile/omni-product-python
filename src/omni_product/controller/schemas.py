from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from omni_product.model import Price, Product, RegionSupplier, Supplier, Warehouse


class CamelModel(BaseModel):
    """JSON en camelCase comme Jackson, attributs Python en snake_case."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class PriceSchema(CamelModel):
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


class WarehouseSchema(CamelModel):
    location: str | None = None


class RegionSupplierSchema(CamelModel):
    name: str | None = None
    siren: str | None = None
    tva_id: str | None = None


class ProductSchema(CamelModel):
    id: str | None = None
    name: str | None = None
    slug: str | None = None
    price: PriceSchema | None = None
    discounts: list[str] | None = None
    images: dict[str, str | None] | None = None
    suppliers_regions: dict[str, RegionSupplierSchema] | None = None
    kilos: float | None = None
    volume: str | None = None
    quantity: int | None = None
    stock: int | None = None
    warehouse: WarehouseSchema | None = None
    supplier_id: str | None = None


class SupplierSchema(CamelModel):
    id: str
    name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    country: str | None = None
    region: str | None = None


class SupplierRequest(CamelModel):
    id: str
    name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    country: str | None = None
    region: str | None = None


class SupplierUpdateRequest(CamelModel):
    name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    country: str | None = None
    region: str | None = None


def product_to_schema(product: Product) -> ProductSchema:
    return ProductSchema(
        id=product.id,
        name=product.name,
        slug=product.slug,
        price=PriceSchema.model_validate(product.price) if product.price else None,
        discounts=list(product.discounts),
        images=dict(product.images),
        suppliers_regions={
            region: RegionSupplierSchema.model_validate(supplier)
            for region, supplier in product.suppliers_regions.items()
        },
        kilos=product.kilos,
        volume=product.volume,
        quantity=product.quantity,
        stock=product.stock,
        warehouse=WarehouseSchema.model_validate(product.warehouse) if product.warehouse else None,
        supplier_id=product.supplier_id,
    )


def schema_to_product(schema: ProductSchema, product_id: str) -> Product:
    """Construit une entité neuve ; `save` la fusionne avec l'existante (comme `PUT` en Java)."""
    product = Product(
        id=product_id,
        name=schema.name,
        slug=schema.slug,
        kilos=schema.kilos,
        volume=schema.volume,
        quantity=schema.quantity,
        stock=schema.stock,
        supplier_id=schema.supplier_id,
    )
    if schema.price is not None:
        product.price = Price(**schema.price.model_dump())
    if schema.warehouse is not None:
        product.warehouse = Warehouse(**schema.warehouse.model_dump())
    product.discounts = schema.discounts or []
    product.images = schema.images or {}
    product.suppliers_regions = {
        region: RegionSupplier(**supplier.model_dump())
        for region, supplier in (schema.suppliers_regions or {}).items()
    }
    return product


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema.model_validate(supplier)
