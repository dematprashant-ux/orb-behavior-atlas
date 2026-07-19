"""Batch read-only canonical quality assessment."""

from collections.abc import Sequence

from src.engines.data.models import Session
from src.engines.data.quality._models import DataQualityReport
from src.engines.data.quality._session import assess_session


def assess_sessions(sessions: Sequence[Session]) -> DataQualityReport:
    """Assess sessions in their supplied order without reconstruction or sorting."""
    if not isinstance(sessions, Sequence):
        raise TypeError("sessions must be a Sequence of Session instances")
    if any(not isinstance(session, Session) for session in sessions):
        raise TypeError("sessions must be a Sequence of Session instances")

    return DataQualityReport(sessions=tuple(assess_session(session) for session in sessions))
