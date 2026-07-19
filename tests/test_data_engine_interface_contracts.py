"""Public contract tests for M2.3 Data Engine interfaces."""

from collections.abc import Sequence
from datetime import date
from inspect import Parameter, Signature, signature
from typing import get_type_hints
import unittest

from src.engines.data import (
    Candle,
    DataAccess,
    DataEngine,
    DataSource,
    Instrument,
    Session,
    Timeframe,
)


class DataEngineInterfaceContractTests(unittest.TestCase):
    """Verify the typed public Data Engine interface surface."""

    def test_data_source_fetch_contract(self) -> None:
        """Require a typed, inclusive session-date source query."""
        method_signature = signature(DataSource.fetch)
        self.assertEqual(
            list(method_signature.parameters),
            ["self", "instrument", "timeframe", "start_date", "end_date"],
        )
        self._assert_keyword_only(
            method_signature,
            "instrument",
            "timeframe",
            "start_date",
            "end_date",
        )
        self.assertEqual(
            get_type_hints(DataSource.fetch),
            {
                "instrument": Instrument,
                "timeframe": Timeframe,
                "start_date": date,
                "end_date": date,
                "return": Sequence[Candle],
            },
        )

    def test_data_access_contract_distinguishes_session_and_range_queries(self) -> None:
        """Keep single-session and multi-session queries as separate public operations."""
        self._assert_keyword_only(
            signature(DataAccess.get_session),
            "instrument",
            "timeframe",
            "session_date",
        )
        self._assert_keyword_only(
            signature(DataAccess.get_candles),
            "instrument",
            "timeframe",
            "session_date",
        )
        self._assert_keyword_only(
            signature(DataAccess.get_date_range),
            "instrument",
            "timeframe",
            "start_date",
            "end_date",
        )
        self.assertEqual(
            get_type_hints(DataAccess.get_session),
            {
                "instrument": Instrument,
                "timeframe": Timeframe,
                "session_date": date,
                "return": Session,
            },
        )
        self.assertEqual(
            get_type_hints(DataAccess.get_candles)["return"],
            Sequence[Candle],
        )
        self.assertEqual(
            get_type_hints(DataAccess.get_date_range)["return"],
            Sequence[Candle],
        )

    def test_data_engine_load_contract_and_deferred_operations(self) -> None:
        """Expose source orchestration while deferring undefined result contracts."""
        method_signature = signature(DataEngine.load_data)
        self.assertEqual(
            list(method_signature.parameters),
            ["self", "source", "instrument", "timeframe", "start_date", "end_date"],
        )
        self.assertIs(
            method_signature.parameters["source"].kind,
            Parameter.POSITIONAL_OR_KEYWORD,
        )
        self.assertIs(method_signature.parameters["source"].default, Parameter.empty)
        self._assert_keyword_only(
            method_signature,
            "instrument",
            "timeframe",
            "start_date",
            "end_date",
        )
        self.assertEqual(
            get_type_hints(DataEngine.load_data),
            {
                "source": DataSource,
                "instrument": Instrument,
                "timeframe": Timeframe,
                "start_date": date,
                "end_date": date,
                "return": Sequence[Candle],
            },
        )
        self.assertFalse(hasattr(DataAccess, "quality_report"))
        self.assertFalse(hasattr(DataEngine, "quality_report"))
        self.assertFalse(hasattr(DataEngine, "validate_data"))

    def _assert_keyword_only(
        self,
        method_signature: Signature,
        *parameter_names: str,
    ) -> None:
        """Verify that public query parameters cannot be passed positionally."""
        for parameter_name in parameter_names:
            parameter = method_signature.parameters[parameter_name]
            self.assertIs(parameter.kind, Parameter.KEYWORD_ONLY)
            self.assertIs(parameter.default, Parameter.empty)


if __name__ == "__main__":
    unittest.main()
