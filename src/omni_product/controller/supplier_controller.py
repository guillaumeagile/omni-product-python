"""Contrôleur minimal des fournisseurs.

Il traduit les `Result` du service en paires (statut HTTP, corps JSON). Il ne dépend d'aucun
framework : une route HTTP peut l'envelopper sans changer ces règles de traduction.
"""

from __future__ import annotations

from result import Err, Ok

from omni_product.domain.model import Supplier
from omni_product.domain.model.errors import ErreurIntrouvable, InvalidValueError
from omni_product.service.supplier_service import SupplierService

Reponse = tuple[int, object]


def _vers_json(supplier: Supplier) -> dict[str, str]:
    return {"id": supplier.id.value, "name": supplier.name}


def _erreur(erreur: InvalidValueError | ErreurIntrouvable) -> Reponse:
    match erreur:
        case ErreurIntrouvable():
            return 404, {"detail": str(erreur)}
        case _:
            return 422, {"detail": str(erreur)}


def create_supplier(service: SupplierService, id: str, name: str) -> Reponse:
    match service.create_supplier(id, name):
        case Ok(supplier):
            return 201, _vers_json(supplier)
        case Err(erreur):
            return _erreur(erreur)


def get_supplier(service: SupplierService, supplier_id: str) -> Reponse:
    match service.get_supplier(supplier_id):
        case Ok(supplier) if supplier is not None:
            return 200, _vers_json(supplier)
        case Ok(_):
            return 404, {"detail": "Supplier not found"}
        case Err(erreur):
            return _erreur(erreur)


def get_all_suppliers(service: SupplierService) -> Reponse:
    return 200, [_vers_json(s) for s in service.get_all_suppliers()]


def get_suppliers_by_product(service: SupplierService, product_id: str) -> Reponse:
    match service.get_suppliers_by_product(product_id):
        case Ok(suppliers):
            return 200, [_vers_json(s) for s in suppliers]
        case Err(erreur):
            return _erreur(erreur)


def update_supplier(service: SupplierService, id: str, name: str | None) -> Reponse:
    match service.update_supplier(id, name):
        case Ok(supplier):
            return 200, _vers_json(supplier)
        case Err(erreur):
            return _erreur(erreur)


def delete_supplier(service: SupplierService, supplier_id: str) -> Reponse:
    match service.delete_supplier(supplier_id):
        case Ok(_):
            return 204, None
        case Err(erreur):
            return _erreur(erreur)
