class InvalidValueError(ValueError):
    """Une valeur du domaine viole son invariant : montant négatif, texte vide, taux hors [0, 1].

    Chaque contexte a sa propre sous-classe : un appelant voit de quel contexte vient l'échec.
    """


class ErreurProduit(InvalidValueError):
    """Contexte Catalogue : identifiant, slug, images, durée de conservation."""


class ErreurFournisseur(InvalidValueError):
    """Contexte Approvisionnement : fournisseur, SIREN, TVA, contacts, pays, région."""


class ErreurTransport(InvalidValueError):
    """Contexte Transport : mode, distance, poids, volume, émissions."""


class ErreurStock(InvalidValueError):
    """Contexte Stockage : quantité, stock, emplacement."""


class ErreurTarification(InvalidValueError):
    """Contexte Prix : montant, taux, remise."""


class ErreurIntrouvable(ValueError):
    """Un identifiant bien formé, qui ne correspond à aucun élément."""
