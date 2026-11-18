from datetime import date


class SystemClock:
    """Implémente `Clock` avec l'horloge du système."""

    def today(self) -> date:
        return date.today()
