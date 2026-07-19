"""Public contracts for the Data Engine architecture.

Concrete data records, sessions, and quality reports are intentionally generic.
They belong to later Data Engine milestones, not to M2.1.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Optional, Protocol, TypeVar

SourceRecordT = TypeVar("SourceRecordT", covariant=True)
AccessRecordT = TypeVar("AccessRecordT", covariant=True)
EngineRecordT = TypeVar("EngineRecordT")
SessionT = TypeVar("SessionT", covariant=True)
QualityReportT = TypeVar("QualityReportT", covariant=True)


class DataSource(Protocol[SourceRecordT]):
    """Defines a provider-neutral boundary for acquiring market-data records."""

    def fetch(
        self,
        *,
        instrument: str,
        timeframe: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Sequence[SourceRecordT]:
        """Return records for the requested instrument, timeframe, and date range."""


class DataAccess(Protocol[AccessRecordT, SessionT, QualityReportT]):
    """Defines provider- and persistence-neutral Data Engine retrieval contracts."""

    def get_session(
        self,
        *,
        instrument: str,
        timeframe: str,
        session_date: date,
    ) -> SessionT:
        """Return the requested trading session."""

    def get_candles(
        self,
        *,
        instrument: str,
        timeframe: str,
        session_date: date,
    ) -> Sequence[AccessRecordT]:
        """Return records associated with the requested trading session."""

    def get_date_range(
        self,
        *,
        instrument: str,
        timeframe: str,
        start_date: date,
        end_date: date,
    ) -> Sequence[AccessRecordT]:
        """Return records within the requested inclusive date range."""

    def quality_report(
        self,
        *,
        instrument: str,
        timeframe: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> QualityReportT:
        """Return a quality report for the requested data scope."""


class DataEngine(Protocol[EngineRecordT, SessionT, QualityReportT]):
    """Defines the future public Data Engine API without providing behavior."""

    def load_data(
        self,
        source: DataSource[EngineRecordT],
        *,
        instrument: str,
        timeframe: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Sequence[EngineRecordT]:
        """Load records from a provider-neutral source boundary."""

    def validate_data(self, records: Sequence[EngineRecordT]) -> QualityReportT:
        """Validate records and return their future quality-report contract."""

    def get_session(
        self,
        *,
        instrument: str,
        timeframe: str,
        session_date: date,
    ) -> SessionT:
        """Return the requested trading session."""

    def get_candles(
        self,
        *,
        instrument: str,
        timeframe: str,
        session_date: date,
    ) -> Sequence[EngineRecordT]:
        """Return records associated with the requested trading session."""

    def get_date_range(
        self,
        *,
        instrument: str,
        timeframe: str,
        start_date: date,
        end_date: date,
    ) -> Sequence[EngineRecordT]:
        """Return records within the requested inclusive date range."""

    def quality_report(
        self,
        *,
        instrument: str,
        timeframe: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> QualityReportT:
        """Return a quality report for the requested data scope."""


__all__ = [
    "AccessRecordT",
    "DataAccess",
    "DataEngine",
    "DataSource",
    "EngineRecordT",
    "QualityReportT",
    "SessionT",
    "SourceRecordT",
]
