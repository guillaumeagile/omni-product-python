class InvalidValueError(ValueError):
    """Une valeur du domaine viole son invariant : montant négatif, texte vide, taux hors [0, 1]."""
