"""Single-session read-only canonical quality assessment."""

from src.engines.data.models import Session
from src.engines.data.quality._models import SessionQualityMetrics, SessionQualityResult
from src.engines.data.quality._rules import unexpected_interval_issue


def assess_session(session: Session) -> SessionQualityResult:
    """Assess supplied canonical session spacing without changing its contents."""
    if not isinstance(session, Session):
        raise TypeError("session must be a Session")

    expected_interval = session.timeframe.duration
    issues = tuple(
        issue
        for previous, current in zip(session.candles, session.candles[1:])
        if (
            issue := unexpected_interval_issue(
                previous_timestamp=previous.timestamp,
                current_timestamp=current.timestamp,
                expected_interval=expected_interval,
            )
        )
        is not None
    )
    first_timestamp = session.candles[0].timestamp if session.candles else None
    last_timestamp = session.candles[-1].timestamp if session.candles else None

    return SessionQualityResult(
        session=session,
        metrics=SessionQualityMetrics(
            candle_count=len(session.candles),
            unexpected_interval_count=len(issues),
            first_timestamp=first_timestamp,
            last_timestamp=last_timestamp,
        ),
        issues=issues,
    )
