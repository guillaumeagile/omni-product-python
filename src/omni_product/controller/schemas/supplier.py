from omni_product.controller.schemas.base import CamelModel


class SupplierUpdateRequest(CamelModel):
    name: str | None = None


class SupplierRequest(CamelModel):
    id: str
    name: str


class SupplierSchema(SupplierRequest):
    """Même forme que la requête de création, pour ne pas recopier les deux champs."""
