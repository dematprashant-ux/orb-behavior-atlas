"""Public session-construction operations."""

from collections.abc import Mapping, Sequence
from datetime import date

from src.engines.data.exceptions import SessionConstructionError
from src.engines.data.models import Candle, Instrument, Session, Timeframe, Weekday
from src.engines.data.sessions._grouping import (
    SessionKey,
    require_homogeneous,
    session_key,
    sorted_session_keys,
)
from src.engines.data.sessions._metadata import SessionMetadata
from src.engines.data.sessions._ordering import require_strictly_increasing

_WEEKDAYS = (
    Weekday.MONDAY,
    Weekday.TUESDAY,
    Weekday.WEDNESDAY,
    Weekday.THURSDAY,
    Weekday.FRIDAY,
)


def build_session(
    candles: Sequence[Candle], *, metadata: SessionMetadata | None = None
) -> Session:
    """Build one immutable session from canonically ordered candles.

    The supplied candle order is preserved. This function does not invoke
    validation or infer any expiry or holiday metadata.
    """
    _require_candles(candles)
    _require_metadata(metadata)

    session_date, instrument, timeframe = require_homogeneous(candles)
    require_strictly_increasing(candles)
    resolved_metadata = metadata or SessionMetadata()

    return Session(
        session_date=session_date,
        instrument=instrument,
        timeframe=timeframe,
        weekday=_weekday_for(session_date),
        is_weekly_expiry=resolved_metadata.is_weekly_expiry,
        is_monthly_expiry=resolved_metadata.is_monthly_expiry,
        has_holiday_gap=resolved_metadata.has_holiday_gap,
        candles=tuple(candles),
    )


def build_sessions(
    candles: Sequence[Candle], *,
    metadata_by_session: Mapping[SessionKey, SessionMetadata] | None = None,
) -> tuple[Session, ...]:
    """Build deterministically ordered sessions without reordering candles."""
    _require_candle_sequence(candles)
    _require_metadata_mapping(metadata_by_session)

    groups: dict[SessionKey, list[Candle]] = {}
    for candle in candles:
        groups.setdefault(session_key(candle), []).append(candle)

    if metadata_by_session and set(metadata_by_session).difference(groups):
        raise SessionConstructionError(
            "Session metadata contains entries for unconstructed sessions."
        )

    metadata = metadata_by_session or {}
    return tuple(
        build_session(groups[key], metadata=metadata.get(key))
        for key in sorted_session_keys(tuple(groups))
    )


def _require_candles(candles: Sequence[Candle]) -> None:
    """Require a non-empty sequence of canonical candle objects."""
    _require_candle_sequence(candles)
    if not candles:
        raise SessionConstructionError("A session requires at least one candle.")


def _require_candle_sequence(candles: Sequence[Candle]) -> None:
    """Reject values outside the session-construction input contract."""
    if not isinstance(candles, Sequence):
        raise TypeError("Candles must be provided as a Sequence.")
    if any(not isinstance(candle, Candle) for candle in candles):
        raise TypeError("Session construction requires canonical Candle objects.")


def _require_metadata(metadata: SessionMetadata | None) -> None:
    """Reject invalid single-session metadata arguments."""
    if metadata is not None and not isinstance(metadata, SessionMetadata):
        raise TypeError("Session metadata must be a SessionMetadata instance or None.")


def _require_metadata_mapping(
    metadata_by_session: Mapping[SessionKey, SessionMetadata] | None,
) -> None:
    """Reject invalid metadata mappings before construction begins."""
    if metadata_by_session is None:
        return
    if not isinstance(metadata_by_session, Mapping):
        raise TypeError("Session metadata must be provided as a Mapping or None.")
    for key, metadata in metadata_by_session.items():
        if not _is_session_key(key) or not isinstance(metadata, SessionMetadata):
            raise TypeError(
                "Session metadata entries must use SessionKey and SessionMetadata values."
            )


def _is_session_key(value: object) -> bool:
    """Return whether a value is a valid canonical session metadata key."""
    return (
        isinstance(value, tuple)
        and len(value) == 3
        and isinstance(value[0], date)
        and isinstance(value[1], Instrument)
        and isinstance(value[2], Timeframe)
    )


def _weekday_for(session_date: date) -> Weekday:
    """Map weekday session dates without inferring an exchange calendar."""
    if session_date.weekday() > 4:
        raise SessionConstructionError("Session date must be a weekday.")
    return _WEEKDAYS[session_date.weekday()]
