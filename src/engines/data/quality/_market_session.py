"""Deterministic BANKNIFTY M5 market-session quality evaluation."""

from collections.abc import Sequence
from datetime import datetime, time
from zoneinfo import ZoneInfo

from src.engines.data.models import Session
from src.engines.data.quality._models import (
    MarketSessionQualityResult,
    MarketSessionQualityStatus,
    MarketSessionRejection,
    MarketSessionRejectionCode,
)
from src.engines.data.quality._session import assess_session
from src.engines.data.validation import validate_candles

__all__ = ["evaluate_market_session_quality", "evaluate_market_session_qualities"]

_MARKET_TIMEZONE = ZoneInfo("Asia/Kolkata")
_SESSION_START = time(9, 15)
_SESSION_END = time(15, 30)


def evaluate_market_session_quality(session: Session) -> MarketSessionQualityResult:
    """Classify one constructed session against BANKNIFTY M5 market policy.

    This function reuses canonical candle validation and observational spacing
    assessment. It does not construct, repair, reorder, or mutate sessions.
    """
    if not isinstance(session, Session):
        raise TypeError("session must be a Session")
    if not session.candles:
        return _rejected(session, ((MarketSessionRejectionCode.EMPTY_SESSION, None),))

    validation_rejections = _validation_rejections(session)
    if validation_rejections:
        return _rejected(session, validation_rejections)

    timestamp_rejections = _timestamp_rejections(session)
    if timestamp_rejections:
        return _rejected(session, timestamp_rejections)

    gap_rejections = _gap_rejections(session)
    if gap_rejections:
        return _rejected(session, gap_rejections)

    status = (
        MarketSessionQualityStatus.VALID_COMPLETE_SESSION
        if _is_complete(session)
        else MarketSessionQualityStatus.VALID_PARTIAL_SESSION
    )
    return MarketSessionQualityResult(session=session, status=status, rejections=())


def evaluate_market_session_qualities(
    sessions: Sequence[Session],
) -> tuple[MarketSessionQualityResult, ...]:
    """Evaluate supplied sessions in their existing deterministic order."""
    if not isinstance(sessions, Sequence):
        raise TypeError("sessions must be a Sequence of Session instances")
    if any(not isinstance(session, Session) for session in sessions):
        raise TypeError("sessions must be a Sequence of Session instances")
    return tuple(evaluate_market_session_quality(session) for session in sessions)


def _validation_rejections(
    session: Session,
) -> tuple[tuple[MarketSessionRejectionCode, str | None], ...]:
    """Project existing semantic validation findings into stable gate reasons."""
    return tuple(
        (MarketSessionRejectionCode.CANDLE_VALIDATION, issue.code.value)
        for result in validate_candles(session.candles)
        for issue in result.issues
    )


def _timestamp_rejections(
    session: Session,
) -> tuple[tuple[MarketSessionRejectionCode, str | None], ...]:
    """Reject timestamps outside or misaligned with the documented M5 session."""
    session_start, session_end = _session_bounds(session)
    rejections: list[tuple[MarketSessionRejectionCode, str | None]] = []
    for candle in session.candles:
        timestamp = candle.timestamp
        if timestamp < session_start or timestamp >= session_end:
            rejections.append(
                (MarketSessionRejectionCode.OUTSIDE_REGULAR_SESSION, None)
            )
        elif (timestamp - session_start) % session.timeframe.duration:
            rejections.append(
                (MarketSessionRejectionCode.UNALIGNED_M5_TIMESTAMP, None)
            )
    return tuple(rejections)


def _gap_rejections(
    session: Session,
) -> tuple[tuple[MarketSessionRejectionCode, str | None], ...]:
    """Promote existing unexpected-interval observations to gate rejections."""
    return tuple(
        (MarketSessionRejectionCode.INTERNAL_M5_GAP, issue.code.value)
        for issue in assess_session(session).issues
    )


def _is_complete(session: Session) -> bool:
    """Return whether all and only the regular-session bar-open timestamps exist."""
    session_start, session_end = _session_bounds(session)
    expected = tuple(
        session_start + (session.timeframe.duration * index)
        for index in range(
            int((session_end - session_start) / session.timeframe.duration)
        )
    )
    return tuple(candle.timestamp for candle in session.candles) == expected


def _session_bounds(session: Session) -> tuple[datetime, datetime]:
    """Return the regular market interval with an exclusive final bar boundary."""
    return (
        datetime.combine(session.session_date, _SESSION_START, tzinfo=_MARKET_TIMEZONE),
        datetime.combine(session.session_date, _SESSION_END, tzinfo=_MARKET_TIMEZONE),
    )


def _rejected(
    session: Session,
    rejections: tuple[tuple[MarketSessionRejectionCode, str | None], ...],
) -> MarketSessionQualityResult:
    """Build one immutable rejected outcome from ordered stable reason values."""
    return MarketSessionQualityResult(
        session=session,
        status=MarketSessionQualityStatus.REJECTED_SESSION,
        rejections=tuple(
            MarketSessionRejection(code=code, detail=detail)
            for code, detail in rejections
        ),
    )
