"""Provider-neutral value types for the v1 Data Engine domain."""

from enum import Enum


class Instrument(str, Enum):
    """Identifies the sole instrument supported by the v1 research scope."""

    BANKNIFTY = "BANKNIFTY"


class Timeframe(str, Enum):
    """Identifies the sole candle aggregation supported by the v1 research scope."""

    M5 = "M5"


class Weekday(str, Enum):
    """Identifies a weekday associated with a trading session."""

    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"


__all__ = ["Instrument", "Timeframe", "Weekday"]
