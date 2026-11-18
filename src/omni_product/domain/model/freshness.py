"""La fraîcheur d'un produit périssable : combien de jours avant sa date d'expiration.

Code legacy : la fonction lit l'horloge du système. Elle n'appartient à aucune classe, donc les
refactorings des règles 1 à 5 (découper `Product`, Value Objects, `domain/model`, composition,
échecs en valeur) la laissent en place. La règle 6 la vise : l'heure doit entrer par un paramètre
ou par un port `Clock`.
"""

from datetime import date


def days_before_expiry(expiration_date: date) -> int:
    """Jours restants avant l'expiration, négatifs quand la date est passée."""
    return (expiration_date - date.today()).days


def is_expired(expiration_date: date) -> bool:
    return days_before_expiry(expiration_date) < 0
