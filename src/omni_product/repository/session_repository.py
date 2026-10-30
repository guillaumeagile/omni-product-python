from sqlalchemy.orm import Session


class SessionRepository:
    """Socle commun des dépôts : une session, et les écritures validées au même endroit."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _merge_and_commit[T](self, entity: T) -> T:
        saved = self._session.merge(entity)
        self._session.commit()
        return saved

    def _delete_and_commit(self, entity: object) -> None:
        self._session.delete(entity)
        self._session.commit()
