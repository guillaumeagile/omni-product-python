from copy import deepcopy

from omni_product.domain.model import ProductId, Supplier, SupplierId
from omni_product.domain.model.product_sheet import ProductSheet

type ProductTable = dict[ProductId, ProductSheet]
type SupplierTable = dict[SupplierId, Supplier]


class InMemoryProductRepository:
    """Implémente `ProductRepository` en mémoire. Les fiches sont copiées en entrée et en sortie."""

    def __init__(self, products: ProductTable) -> None:
        self._products = products

    def find_all(self) -> list[ProductSheet]:
        ids = sorted(self._products, key=lambda product_id: product_id.value)
        return [deepcopy(self._products[product_id]) for product_id in ids]

    def find_by_id(self, product_id: ProductId) -> ProductSheet | None:
        return deepcopy(self._products.get(product_id))

    def save(self, sheet: ProductSheet) -> ProductSheet:
        self._products[sheet.product.id] = deepcopy(sheet)
        return deepcopy(sheet)

    def delete_by_id(self, product_id: ProductId) -> None:
        self._products.pop(product_id, None)


class InMemorySupplierRepository:
    """Implémente `SupplierRepository` en mémoire. Il lit les fiches des produits."""

    def __init__(self, suppliers: SupplierTable, products: ProductTable) -> None:
        self._suppliers = suppliers
        self._products = products

    def find_all(self) -> list[Supplier]:
        ids = sorted(self._suppliers, key=lambda supplier_id: supplier_id.value)
        return [deepcopy(self._suppliers[supplier_id]) for supplier_id in ids]

    def find_by_id(self, supplier_id: SupplierId) -> Supplier | None:
        return deepcopy(self._suppliers.get(supplier_id))

    def find_by_product_id(self, product_id: ProductId) -> list[Supplier]:
        sheet = self._products.get(product_id)
        supplier_id = None if sheet is None or sheet.supply is None else sheet.supply.supplier_id
        supplier = None if supplier_id is None else self._suppliers.get(supplier_id)
        return [] if supplier is None else [deepcopy(supplier)]

    def save(self, supplier: Supplier) -> Supplier:
        self._suppliers[supplier.id] = deepcopy(supplier)
        return deepcopy(supplier)

    def delete(self, supplier: Supplier) -> None:
        # Comportement conservé : supprimer un fournisseur supprime les produits qu'il fournit.
        for product_id, sheet in list(self._products.items()):
            if sheet.supply is not None and sheet.supply.supplier_id == supplier.id:
                del self._products[product_id]
        self._suppliers.pop(supplier.id, None)
