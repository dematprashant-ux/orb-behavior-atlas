"""Provider-neutral value types for the v1 Data Engine domain."""

from datetime import timedelta
from enum import Enum


class Instrument(str, Enum):
    """Identifies the sole instrument supported by the v1 research scope."""

    BANKNIFTY = "BANKNIFTY"


class Timeframe(str, Enum):
    """Identifies the sole candle aggregation supported by the v1 research scope."""

    M5 = "M5"

    @property
    def duration(self) -> timedelta:
        """Return the canonical interval for this supported timeframe.

        New timeframe members must define a duration before quality assessment
        can evaluate their timestamp spacing.
        """
        try:
            return _TIMEFRAME_DURATIONS[self]
        except KeyError as error:
            raise ValueError(
                f"No canonical duration is configured for timeframe {self.value}."
            ) from error


class Weekday(str, Enum):
    """Identifies a weekday associated with a trading session."""

    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"


_TIMEFRAME_DURATIONS = {
    Timeframe.M5: timedelta(minutes=5),
}


__all__ = ["Instrument", "Timeframe", "Weekday"]
