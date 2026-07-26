class ORBError(Exception):
    """Base project exception."""


class PersistenceError(ORBError):
    """Base error for technology-neutral identity-based persistence failures."""


class PersistenceConflictError(PersistenceError):
    """Raised when storage rejects an already-existing identity."""


class PersistenceNotFoundError(PersistenceError):
    """Raised when storage cannot retrieve a requested identity."""


__all__ = [
    "ORBError",
    "PersistenceConflictError",
    "PersistenceError",
    "PersistenceNotFoundError",
]
