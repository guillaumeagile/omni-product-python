"""La fraîcheur d'un produit périssable : combien de jours avant sa date d'expiration.

L'heure entre par le port `Clock` : le cœur ne lit pas l'horloge du système. Le service fournit
l'horloge réelle, les tests fournissent une horloge figée.
"""

from datetime import date

from omni_product.domain.port.clock import Clock


def days_before_expiry(expiration_date: date, clock: Clock) -> int:
    """Jours restants avant l'expiration, négatifs quand la date est passée."""
    return (expiration_date - clock.today()).days


def is_expired(expiration_date: date, clock: Clock) -> bool:
    return days_before_expiry(expiration_date, clock) < 0
