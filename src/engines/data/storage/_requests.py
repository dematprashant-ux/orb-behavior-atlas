"""Immutable requests for technology-neutral canonical storage operations."""

from dataclasses import dataclass
from datetime import date

from src.engines.data.models import Candle, Instrument, Session, Timeframe
from src.engines.data.storage._identity import CandleIdentity, SessionIdentity


@dataclass(frozen=True, slots=True)
class StoreSessionRequest:
    """Request persistence of one internally consistent canonical session."""

    session: Session

    def __post_init__(self) -> None:
        """Reject malformed aggregates without re-running candle validation."""
        if not isinstance(self.session, Session):
            raise TypeError("session must be a Session")
        _require_consistent_session(self.session)


@dataclass(frozen=True, slots=True)
class LoadSessionRequest:
    """Request one canonical session by its stable storage identity."""

    identity: SessionIdentity

    def __post_init__(self) -> None:
        """Require a canonical session identity."""
        if not isinstance(self.identity, SessionIdentity):
            raise TypeError("identity must be a SessionIdentity")


@dataclass(frozen=True, slots=True)
class LoadCandlesRequest:
    """Request candles within an inclusive canonical session-date range."""

    instrument: Instrument
    timeframe: Timeframe
    start_session_date: date
    end_session_date: date

    def __post_init__(self) -> None:
        """Reject ranges whose inclusive boundaries are reversed."""
        if self.start_session_date > self.end_session_date:
            raise ValueError("start_session_date must not be after end_session_date")


def _require_consistent_session(session: Session) -> None:
    """Enforce storage aggregate identity and ordering invariants only."""
    candle_identities: set[CandleIdentity] = set()
    previous_timestamp = None

    for candle in session.candles:
        _require_canonical_candle(candle)
        if (
            candle.instrument != session.instrument
            or candle.timeframe != session.timeframe
            or candle.session_date != session.session_date
        ):
            raise ValueError("session candles must match the session identity")

        identity = CandleIdentity(candle.instrument, candle.timeframe, candle.timestamp)
        if identity in candle_identities:
            raise ValueError("session candles must have unique identities")
        candle_identities.add(identity)

        if previous_timestamp is not None and candle.timestamp <= previous_timestamp:
            raise ValueError("session candles must have strictly increasing timestamps")
        previous_timestamp = candle.timestamp


def _require_canonical_candle(candle: Candle) -> None:
    """Require a candle object without evaluating its semantic market validity."""
    if not isinstance(candle, Candle):
        raise ValueError("session candles must be Candle objects")
