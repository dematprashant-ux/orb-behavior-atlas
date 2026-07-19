"""Deterministic composition of the completed Data Engine capabilities."""

from src.engines.data.interfaces import DataSource
from src.engines.data.orchestration._models import (
    DataEngineExecutionRequest,
    DataEngineExecutionResult,
    ExecutionStage,
    ExecutionStatus,
)
from src.engines.data.quality import DataQualityReport, assess_sessions
from src.engines.data.sessions import build_sessions
from src.engines.data.storage import DataStore, SessionIdentity, StoreSessionRequest
from src.engines.data.validation import CandleValidationResult, validate_candles
from src.engines.data.models import Candle, Session


class DataEngineOrchestrator:
    """Coordinates canonical data processing without duplicating component logic."""

    def __init__(self, *, data_store: DataStore | None = None) -> None:
        """Create an orchestrator with optional storage persistence capability."""
        self._data_store = data_store

    def execute(
        self,
        source: DataSource,
        request: DataEngineExecutionRequest,
    ) -> DataEngineExecutionResult:
        """Run fetch, validation, construction, quality, and optional persistence."""
        if not isinstance(request, DataEngineExecutionRequest):
            raise TypeError("request must be a DataEngineExecutionRequest")

        candles: tuple[Candle, ...] = ()
        validation_results: tuple[CandleValidationResult, ...] = ()
        sessions: tuple[Session, ...] = ()
        quality_report = DataQualityReport(())
        persisted_session_identities: tuple[SessionIdentity, ...] = ()

        try:
            candles = tuple(
                source.fetch(
                    instrument=request.instrument,
                    timeframe=request.timeframe,
                    start_date=request.start_date,
                    end_date=request.end_date,
                )
            )
        except Exception:
            return self._failed_result(
                request,
                candles,
                validation_results,
                sessions,
                quality_report,
                persisted_session_identities,
                ExecutionStage.FETCH,
            )

        try:
            validation_results = validate_candles(candles)
        except Exception:
            return self._failed_result(
                request,
                candles,
                validation_results,
                sessions,
                quality_report,
                persisted_session_identities,
                ExecutionStage.VALIDATION,
            )

        if any(not result.is_valid for result in validation_results):
            return DataEngineExecutionResult(
                request=request,
                status=ExecutionStatus.REJECTED,
                candles=candles,
                validation_results=validation_results,
                sessions=sessions,
                quality_report=quality_report,
                persisted_session_identities=persisted_session_identities,
            )

        try:
            sessions = build_sessions(candles)
        except Exception:
            return self._failed_result(
                request,
                candles,
                validation_results,
                sessions,
                quality_report,
                persisted_session_identities,
                ExecutionStage.SESSION_CONSTRUCTION,
            )

        try:
            quality_report = assess_sessions(sessions)
        except Exception:
            return self._failed_result(
                request,
                candles,
                validation_results,
                sessions,
                quality_report,
                persisted_session_identities,
                ExecutionStage.QUALITY_ASSESSMENT,
            )

        if self._data_store is not None:
            persisted: list[SessionIdentity] = []
            try:
                for session in sessions:
                    persisted.append(
                        self._data_store.store_session(
                            StoreSessionRequest(session)
                        ).identity
                    )
            except Exception:
                return self._failed_result(
                    request,
                    candles,
                    validation_results,
                    sessions,
                    quality_report,
                    tuple(persisted),
                    ExecutionStage.PERSISTENCE,
                )
            persisted_session_identities = tuple(persisted)

        return DataEngineExecutionResult(
            request=request,
            status=ExecutionStatus.COMPLETED,
            candles=candles,
            validation_results=validation_results,
            sessions=sessions,
            quality_report=quality_report,
            persisted_session_identities=persisted_session_identities,
        )

    def _failed_result(
        self,
        request: DataEngineExecutionRequest,
        candles: tuple[Candle, ...],
        validation_results: tuple[CandleValidationResult, ...],
        sessions: tuple[Session, ...],
        quality_report: DataQualityReport,
        persisted_session_identities: tuple[SessionIdentity, ...],
        failure_stage: ExecutionStage,
    ) -> DataEngineExecutionResult:
        """Return a safe immutable failure result without exposing exception details."""
        return DataEngineExecutionResult(
            request=request,
            status=ExecutionStatus.FAILED,
            candles=candles,
            validation_results=validation_results,
            sessions=sessions,
            quality_report=quality_report,
            persisted_session_identities=persisted_session_identities,
            failure_stage=failure_stage,
        )
