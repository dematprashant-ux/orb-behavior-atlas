"""Contract tests for M3.1 deterministic Data Engine orchestration."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime
from inspect import Parameter, signature
from typing import get_type_hints
from unittest.mock import patch
from zoneinfo import ZoneInfo
import unittest

from src.engines.data import (
    Candle,
    DataEngineExecutionRequest,
    DataEngineExecutionResult,
    DataEngineOrchestrator,
    ExecutionStage,
    ExecutionStatus,
    Instrument,
    SessionIdentity,
    StoreSessionResult,
    Timeframe,
)


class DataEngineOrchestrationContractTests(unittest.TestCase):
    """Verify orchestration composes existing Data Engine capabilities only."""

    def test_execution_models_and_service_surface_are_typed_and_immutable(self) -> None:
        """Expose one request, result, and deterministic application service."""
        request = _request()
        result = DataEngineOrchestrator().execute(_StaticSource((_candle(),)), request)

        self.assertEqual(list(ExecutionStatus), [
            ExecutionStatus.COMPLETED,
            ExecutionStatus.REJECTED,
            ExecutionStatus.FAILED,
        ])
        self.assertTrue(is_dataclass(request))
        self.assertTrue(is_dataclass(result))
        with self.assertRaises(FrozenInstanceError):
            request.start_date = date(2026, 7, 18)

        method_signature = signature(DataEngineOrchestrator.execute)
        self.assertEqual(list(method_signature.parameters), ["self", "source", "request"])
        self.assertIs(
            method_signature.parameters["source"].kind,
            Parameter.POSITIONAL_OR_KEYWORD,
        )
        self.assertEqual(
            get_type_hints(DataEngineOrchestrator.execute)["return"],
            DataEngineExecutionResult,
        )

    def test_completed_execution_composes_existing_steps_in_order(self) -> None:
        """Fetch, validate, construct, assess, and return immutable outputs."""
        source = _StaticSource((_candle(minute=15), _candle(minute=20)))

        result = DataEngineOrchestrator().execute(source, _request())

        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertIsNone(result.failure_stage)
        self.assertEqual(result.candles, source.candles)
        self.assertEqual(len(result.validation_results), 2)
        self.assertEqual(len(result.sessions), 1)
        self.assertEqual(result.quality_report.session_count, 1)
        self.assertEqual(result.persisted_session_identities, ())

    def test_invalid_candles_are_rejected_before_all_later_stages(self) -> None:
        """v1 never allows invalid canonical candles to continue through the pipeline."""
        invalid = _candle(high=90.0)

        result = DataEngineOrchestrator().execute(_StaticSource((invalid,)), _request())

        self.assertEqual(result.status, ExecutionStatus.REJECTED)
        self.assertIsNone(result.failure_stage)
        self.assertEqual(len(result.validation_results), 1)
        self.assertFalse(result.validation_results[0].is_valid)
        self.assertEqual(result.sessions, ())
        self.assertEqual(result.quality_report.sessions, ())
        self.assertEqual(result.persisted_session_identities, ())

    def test_data_store_presence_controls_deterministic_persistence(self) -> None:
        """Persist all successfully constructed sessions only when a store is wired."""
        store = _RecordingStore()
        source = _StaticSource(
            (
                _candle(session_date=date(2026, 7, 17), minute=15),
                _candle(session_date=date(2026, 7, 20), minute=15),
            )
        )

        result = DataEngineOrchestrator(data_store=store).execute(source, _request())

        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(
            [identity.session_date for identity in result.persisted_session_identities],
            [date(2026, 7, 17), date(2026, 7, 20)],
        )
        self.assertEqual(store.stored_identities, result.persisted_session_identities)

    def test_provider_failure_returns_a_safe_failed_result(self) -> None:
        """Convert provider failures to status without exposing provider exception text."""
        result = DataEngineOrchestrator().execute(_FailingSource(), _request())

        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertEqual(result.failure_stage, ExecutionStage.FETCH)
        self.assertEqual(result.candles, ())
        self.assertEqual(result.validation_results, ())

    def test_session_construction_failure_returns_failed_result(self) -> None:
        """Keep construction errors out of later quality and persistence stages."""
        saturday = _candle(session_date=date(2026, 7, 18), minute=15)

        result = DataEngineOrchestrator().execute(_StaticSource((saturday,)), _request())

        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertEqual(result.failure_stage, ExecutionStage.SESSION_CONSTRUCTION)
        self.assertEqual(result.sessions, ())
        self.assertEqual(result.quality_report.sessions, ())

    def test_persistence_failure_returns_completed_prior_output_as_failed(self) -> None:
        """Expose no rollback guarantee while preserving completed prior-stage outputs."""
        source = _StaticSource((_candle(minute=15),))

        result = DataEngineOrchestrator(data_store=_FailingStore()).execute(source, _request())

        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertEqual(result.failure_stage, ExecutionStage.PERSISTENCE)
        self.assertEqual(len(result.sessions), 1)
        self.assertEqual(result.quality_report.session_count, 1)
        self.assertEqual(result.persisted_session_identities, ())

    def test_invalid_execution_request_is_a_programming_error(self) -> None:
        """Keep invalid API arguments outside the terminal execution-result path."""
        with self.assertRaises(TypeError):
            DataEngineOrchestrator().execute(_StaticSource((_candle(),)), "request")


class _StaticSource:
    """Minimal canonical DataSource fixture with deterministic payloads."""

    def __init__(self, candles: tuple[Candle, ...]) -> None:
        self.candles = candles

    def fetch(
        self,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
        start_date: date,
        end_date: date,
    ) -> tuple[Candle, ...]:
        """Return configured canonical candles without provider behavior."""
        return self.candles


class _FailingSource:
    """Minimal source fixture that represents a provider-access failure."""

    def fetch(
        self,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
        start_date: date,
        end_date: date,
    ) -> tuple[Candle, ...]:
        """Raise an intentionally non-public failure message."""
        raise RuntimeError("provider secret")


class _RecordingStore:
    """Minimal store fixture that records deterministic session writes."""

    def __init__(self) -> None:
        self.stored_identities: tuple[SessionIdentity, ...] = ()

    def store_session(self, request: object) -> StoreSessionResult:
        """Record one supplied storage request identity."""
        identity = SessionIdentity(
            request.session.session_date,
            request.session.instrument,
            request.session.timeframe,
        )
        self.stored_identities += (identity,)
        return StoreSessionResult(identity)


class _FailingStore:
    """Minimal store fixture that represents persistence failure."""

    def store_session(self, request: object) -> StoreSessionResult:
        """Raise an intentionally non-public persistence failure message."""
        raise RuntimeError("storage secret")


def _request() -> DataEngineExecutionRequest:
    """Create the standard inclusive v1 execution request."""
    return DataEngineExecutionRequest(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        start_date=date(2026, 7, 17),
        end_date=date(2026, 7, 20),
    )


def _candle(
    *,
    session_date: date = date(2026, 7, 17),
    minute: int = 15,
    high: float = 101.0,
) -> Candle:
    """Create a canonical candle suitable for orchestration contract tests."""
    return Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=datetime(
            session_date.year,
            session_date.month,
            session_date.day,
            9,
            minute,
            tzinfo=ZoneInfo("Asia/Kolkata"),
        ),
        session_date=session_date,
        open=100.0,
        high=high,
        low=99.0,
        close=100.5,
        volume=1,
    )


if __name__ == "__main__":
    unittest.main()
