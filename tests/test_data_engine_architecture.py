"""Architecture-boundary tests for M2.1."""

import unittest

from src.core.exceptions import ORBError
from src.engines.data import (
    DataAccess,
    DataAccessError,
    DataEngine,
    DataEngineError,
    DataSource,
    DataSourceError,
    UnsupportedInstrumentError,
    UnsupportedTimeframeError,
)


class DataEngineArchitectureTests(unittest.TestCase):
    """Verify that the M2.1 public architecture surface is importable."""

    def test_data_engine_contracts_are_importable(self) -> None:
        """Expose the three Data Engine contracts from the stable package entry point."""
        self.assertTrue(DataSource)
        self.assertTrue(DataAccess)
        self.assertTrue(DataEngine)

    def test_data_engine_exceptions_share_the_project_base_exception(self) -> None:
        """Keep all Data Engine failures inside the project exception hierarchy."""
        for exception_type in (
            DataEngineError,
            DataSourceError,
            DataAccessError,
            UnsupportedInstrumentError,
            UnsupportedTimeframeError,
        ):
            self.assertTrue(issubclass(exception_type, ORBError))


if __name__ == "__main__":
    unittest.main()
