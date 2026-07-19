"""Immutable public models for deterministic Data Engine orchestration."""

from dataclasses import dataclass
from datetime import date
from enum import Enum

from src.engines.data.models import Candle, Instrument, Session, Timeframe
from src.engines.data.quality import DataQualityReport
from src.engines.data.storage import SessionIdentity
from src.engines.data.validation import CandleValidationResult


class ExecutionStatus(str, Enum):
    """Classifies the terminal state of one orchestration execution."""

    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class ExecutionStage(str, Enum):
    """Identifies the orchestration stage that produced a failed result."""

    FETCH = "FETCH"
    VALIDATION = "VALIDATION"
    SESSION_CONSTRUCTION = "SESSION_CONSTRUCTION"
    QUALITY_ASSESSMENT = "QUALITY_ASSESSMENT"
    PERSISTENCE = "PERSISTENCE"


@dataclass(frozen=True, slots=True)
class DataEngineExecutionRequest:
    """Defines one inclusive canonical source request for orchestration."""

    instrument: Instrument
    timeframe: Timeframe
    start_date: date
    end_date: date


@dataclass(frozen=True, slots=True)
class DataEngineExecutionResult:
    """Captures immutable outputs and terminal status of an execution."""

    request: DataEngineExecutionRequest
    status: ExecutionStatus
    candles: tuple[Candle, ...]
    validation_results: tuple[CandleValidationResult, ...]
    sessions: tuple[Session, ...]
    quality_report: DataQualityReport
    persisted_session_identities: tuple[SessionIdentity, ...]
    failure_stage: ExecutionStage | None = None
