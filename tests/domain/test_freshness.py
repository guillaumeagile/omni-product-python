from datetime import date

from omni_product.domain.model import freshness


class FakeClock:
    def __init__(self, today: date) -> None:
        self._today = today

    def today(self) -> date:
        return self._today


def test_days_before_expiry_counts_the_days_left() -> None:
    clock = FakeClock(date(2026, 11, 10))

    assert freshness.days_before_expiry(date(2026, 11, 15), clock) == 5


def test_days_before_expiry_is_negative_once_expired() -> None:
    clock = FakeClock(date(2026, 11, 10))

    assert freshness.days_before_expiry(date(2026, 11, 8), clock) == -2


def test_a_product_is_not_expired_on_its_expiration_date() -> None:
    clock = FakeClock(date(2026, 11, 10))

    assert not freshness.is_expired(date(2026, 11, 10), clock)


def test_a_product_is_expired_the_day_after() -> None:
    clock = FakeClock(date(2026, 11, 11))

    assert freshness.is_expired(date(2026, 11, 10), clock)
