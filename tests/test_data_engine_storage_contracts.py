"""Contract tests for M2.8 technology-neutral Data Engine storage."""

from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import date, datetime
from inspect import Parameter, Signature, signature
from typing import get_type_hints
import unittest

from src.engines.data import (
    Candle,
    CandleIdentity,
    DataAccessError,
    DataStorageConflictError,
    DataStorageCorruptionError,
    DataStorageError,
    DataStore,
    Instrument,
    LoadCandlesRequest,
    LoadCandlesResult,
    LoadSessionRequest,
    LoadSessionResult,
    Session,
    SessionIdentity,
    StoreSessionRequest,
    StoreSessionResult,
    Timeframe,
    Weekday,
)


class DataStorageContractTests(unittest.TestCase):
    """Verify the storage boundary remains canonical and technology-neutral."""

    def test_data_store_protocol_has_the_approved_operations(self) -> None:
        """Keep session writes and canonical retrievals as the entire public protocol."""
        self.assertEqual(
            [name for name in DataStore.__dict__ if not name.startswith("_")],
            ["store_session", "load_session", "load_candles"],
        )
        self._assert_request_signature(
            DataStore.store_session,
            StoreSessionRequest,
            StoreSessionResult,
        )
        self._assert_request_signature(
            DataStore.load_session,
            LoadSessionRequest,
            LoadSessionResult,
        )
        self._assert_request_signature(
            DataStore.load_candles,
            LoadCandlesRequest,
            LoadCandlesResult,
        )

    def test_identity_models_use_the_canonical_storage_keys(self) -> None:
        """Prevent provider identifiers or derived candle fields entering storage identity."""
        self.assertEqual(
            get_type_hints(CandleIdentity),
            {
                "instrument": Instrument,
                "timeframe": Timeframe,
                "timestamp": datetime,
            },
        )
        self.assertEqual(
            get_type_hints(SessionIdentity),
            {
                "session_date": date,
                "instrument": Instrument,
                "timeframe": Timeframe,
            },
        )

    def test_requests_and_results_are_immutable_models(self) -> None:
        """Keep storage-boundary values safe to pass between implementations."""
        models = (
            CandleIdentity(Instrument.BANKNIFTY, Timeframe.M5, datetime(2026, 7, 17, 9, 15)),
            SessionIdentity(date(2026, 7, 17), Instrument.BANKNIFTY, Timeframe.M5),
            StoreSessionRequest(_session()),
            LoadSessionRequest(
                SessionIdentity(date(2026, 7, 17), Instrument.BANKNIFTY, Timeframe.M5)
            ),
            LoadCandlesRequest(
                Instrument.BANKNIFTY,
                Timeframe.M5,
                date(2026, 7, 17),
                date(2026, 7, 17),
            ),
            StoreSessionResult(
                SessionIdentity(date(2026, 7, 17), Instrument.BANKNIFTY, Timeframe.M5)
            ),
            LoadSessionResult(None),
            LoadCandlesResult(()),
        )

        self.assertTrue(all(is_dataclass(model) for model in models))
        with self.assertRaises(FrozenInstanceError):
            models[0].timestamp = datetime(2026, 7, 17, 9, 20)

    def test_load_candles_range_is_inclusive_and_rejects_reversed_dates(self) -> None:
        """Represent same-day ranges and reject impossible inclusive ranges."""
        same_day = LoadCandlesRequest(
            Instrument.BANKNIFTY,
            Timeframe.M5,
            date(2026, 7, 17),
            date(2026, 7, 17),
        )

        self.assertEqual(same_day.start_session_date, same_day.end_session_date)
        with self.assertRaises(ValueError):
            LoadCandlesRequest(
                Instrument.BANKNIFTY,
                Timeframe.M5,
                date(2026, 7, 18),
                date(2026, 7, 17),
            )

    def test_store_request_rejects_malformed_session_aggregates(self) -> None:
        """Check identity and ordering only, without re-running OHLC validation."""
        candle = _candle(minute=15)
        mismatched_date = replace(candle, session_date=date(2026, 7, 20))
        duplicate = _candle(minute=15)
        descending = _candle(minute=10)

        with self.assertRaises(ValueError):
            StoreSessionRequest(_session(candles=(mismatched_date,)))
        with self.assertRaises(ValueError):
            StoreSessionRequest(_session(candles=(candle, duplicate)))
        with self.assertRaises(ValueError):
            StoreSessionRequest(_session(candles=(candle, descending)))

    def test_store_request_does_not_repeat_candle_semantic_validation(self) -> None:
        """Storage checks aggregate structure rather than M2.5 OHLC semantics."""
        invalid_ohlc = replace(_candle(minute=15), high=90.0)

        request = StoreSessionRequest(_session(candles=(invalid_ohlc,)))

        self.assertEqual(request.session.candles, (invalid_ohlc,))

    def test_result_models_represent_absence_and_empty_matches(self) -> None:
        """Keep ordinary missing data outside the storage exception path."""
        self.assertIsNone(LoadSessionResult(None).session)
        self.assertEqual(LoadCandlesResult(()).candles, ())

    def test_candle_result_rejects_backend_ordering_that_is_not_canonical(self) -> None:
        """Require a storage implementation to expose ascending timestamps only."""
        later = _candle(minute=20)
        earlier = _candle(minute=15)

        with self.assertRaises(ValueError):
            LoadCandlesResult((later, earlier))

    def test_storage_errors_extend_the_existing_access_boundary(self) -> None:
        """Keep storage failures inside the established Data Engine hierarchy."""
        self.assertTrue(issubclass(DataStorageError, DataAccessError))
        self.assertTrue(issubclass(DataStorageConflictError, DataStorageError))
        self.assertTrue(issubclass(DataStorageCorruptionError, DataStorageError))

    def _assert_request_signature(
        self,
        method: object,
        request_type: type[object],
        result_type: type[object],
    ) -> None:
        """Verify each storage operation takes one required request object."""
        method_signature = signature(method)
        self.assertEqual(list(method_signature.parameters), ["self", "request"])
        request_parameter = method_signature.parameters["request"]
        self.assertIs(request_parameter.kind, Parameter.POSITIONAL_OR_KEYWORD)
        self.assertIs(request_parameter.default, Parameter.empty)
        self.assertEqual(
            get_type_hints(method),
            {"request": request_type, "return": result_type},
        )


def _session(candles: tuple[Candle, ...] | None = None) -> Session:
    """Create a structurally valid session for storage contract tests."""
    return Session(
        session_date=date(2026, 7, 17),
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        weekday=Weekday.FRIDAY,
        is_weekly_expiry=None,
        is_monthly_expiry=None,
        has_holiday_gap=None,
        candles=candles or (_candle(minute=15),),
    )


def _candle(minute: int) -> Candle:
    """Create a canonical-looking candle without invoking normalization."""
    return Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=datetime(2026, 7, 17, 9, minute),
        session_date=date(2026, 7, 17),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=1,
    )


if __name__ == "__main__":
    unittest.main()
