"""Typed public contracts and provider boundary for the Data Engine.

Provider adapters use Data Engine-owned normalization components internally and
return canonical candles from the ``DataSource`` boundary. Validation, session
construction, quality assessment, storage, and orchestration use separate
public boundaries.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from src.engines.data.models import Candle, Instrument, Session, Timeframe


class DataSource(Protocol):
    """Defines a provider-neutral boundary that returns canonical candles."""

    def fetch(
        self,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
        start_date: date,
        end_date: date,
    ) -> Sequence[Candle]:
        """Return candles whose session dates fall within the inclusive range."""


class DataAccess(Protocol):
    """Defines provider- and persistence-neutral Data Engine retrieval contracts."""

    def get_session(
        self,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
        session_date: date,
    ) -> Session:
        """Return the requested trading session."""

    def get_candles(
        self,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
        session_date: date,
    ) -> Sequence[Candle]:
        """Return records associated with the requested trading session."""

    def get_date_range(
        self,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
        start_date: date,
        end_date: date,
    ) -> Sequence[Candle]:
        """Return records within the requested inclusive date range."""


class DataEngine(DataAccess, Protocol):
    """Defines Data Engine source orchestration without market-data behavior."""

    def load_data(
        self,
        source: DataSource,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
        start_date: date,
        end_date: date,
    ) -> Sequence[Candle]:
        """Load records from a provider-neutral source boundary."""


__all__ = ["DataAccess", "DataEngine", "DataSource"]
