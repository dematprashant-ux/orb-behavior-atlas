"""Private observational rules for canonical session quality assessment."""

from datetime import datetime, timedelta

from src.engines.data.quality._models import QualityCode, QualityIssue, QualitySeverity


def unexpected_interval_issue(
    *,
    previous_timestamp: datetime,
    current_timestamp: datetime,
    expected_interval: timedelta,
) -> QualityIssue | None:
    """Report unexpected timestamp spacing without inferring its cause."""
    observed_interval = current_timestamp - previous_timestamp
    if observed_interval == expected_interval:
        return None

    return QualityIssue(
        code=QualityCode.UNEXPECTED_INTERVAL,
        severity=QualitySeverity.WARNING,
        message="Observed candle interval differs from the canonical timeframe duration.",
        previous_timestamp=previous_timestamp,
        current_timestamp=current_timestamp,
        expected_interval=expected_interval,
        observed_interval=observed_interval,
    )
