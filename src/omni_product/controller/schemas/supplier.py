from omni_product.controller.schemas.base import CamelModel


class SupplierUpdateRequest(CamelModel):
    name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    country: str | None = None
    region: str | None = None


class SupplierRequest(SupplierUpdateRequest):
    id: str


class SupplierSchema(SupplierRequest):
    """Même forme que la requête de création, pour ne pas recopier les cinq champs."""
