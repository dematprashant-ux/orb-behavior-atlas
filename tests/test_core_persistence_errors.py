"""Tests for engine-neutral identity-based persistence error semantics."""

from unittest import TestCase

from src.core.exceptions import (
    ORBError,
    PersistenceConflictError,
    PersistenceError,
    PersistenceNotFoundError,
)
from src.engines.data import DataStorageConflictError


class PersistenceErrorTests(TestCase):
    """Verify generic persistence failures remain independent of engines."""

    def test_shared_persistence_error_hierarchy_is_engine_neutral(self) -> None:
        self.assertTrue(issubclass(PersistenceError, ORBError))
        self.assertTrue(issubclass(PersistenceConflictError, PersistenceError))
        self.assertTrue(issubclass(PersistenceNotFoundError, PersistenceError))
        self.assertTrue(PersistenceError.__module__.startswith("src.core"))
        self.assertTrue(PersistenceConflictError.__module__.startswith("src.core"))
        self.assertTrue(PersistenceNotFoundError.__module__.startswith("src.core"))

    def test_shared_error_messages_are_explicit_and_deterministic(self) -> None:
        conflict = PersistenceConflictError("duplicate identity")
        missing = PersistenceNotFoundError("missing identity")

        self.assertEqual(str(conflict), "duplicate identity")
        self.assertEqual(str(missing), "missing identity")
        self.assertEqual(
            repr(conflict),
            repr(PersistenceConflictError("duplicate identity")),
        )
        self.assertEqual(
            repr(missing),
            repr(PersistenceNotFoundError("missing identity")),
        )

    def test_data_storage_conflict_remains_shared_catchable(self) -> None:
        error = DataStorageConflictError("existing canonical identity")

        self.assertEqual(str(error), "existing canonical identity")
        self.assertTrue(issubclass(DataStorageConflictError, PersistenceConflictError))
        with self.assertRaises(PersistenceConflictError):
            raise error
