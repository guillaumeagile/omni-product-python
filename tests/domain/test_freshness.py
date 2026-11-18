from datetime import date
from unittest.mock import patch

from omni_product.domain.model import freshness


# Legacy : l'horloge se fige avec `patch`.
# La règle 6 supprime ce besoin : l'heure passe en paramètre.
def test_days_before_expiry_counts_the_days_left() -> None:
    with patch.object(freshness, "date") as fake_date:
        fake_date.today.return_value = date(2026, 11, 10)

        assert freshness.days_before_expiry(date(2026, 11, 15)) == 5


def test_days_before_expiry_is_negative_once_expired() -> None:
    with patch.object(freshness, "date") as fake_date:
        fake_date.today.return_value = date(2026, 11, 10)

        assert freshness.days_before_expiry(date(2026, 11, 8)) == -2


def test_a_product_is_not_expired_on_its_expiration_date() -> None:
    with patch.object(freshness, "date") as fake_date:
        fake_date.today.return_value = date(2026, 11, 10)

        assert not freshness.is_expired(date(2026, 11, 10))


def test_a_product_is_expired_the_day_after() -> None:
    with patch.object(freshness, "date") as fake_date:
        fake_date.today.return_value = date(2026, 11, 11)

        assert freshness.is_expired(date(2026, 11, 10))
