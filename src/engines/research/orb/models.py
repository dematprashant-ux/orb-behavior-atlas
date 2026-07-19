"""Immutable observed-fact models for BANKNIFTY ORB research sessions."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.engines.data.models import Candle, Session

__all__ = [
    "OpeningRange",
    "ORBBehavior",
    "ORBBehaviorKind",
    "ORBEscapeDirection",
    "ORBEscapeEvent",
    "ORBPostEscapeObservation",
    "ORBSession",
    "ORBWindow",
]


@dataclass(frozen=True, slots=True)
class ORBWindow:
    """Identifies the canonical timestamp interval observed as an ORB window."""

    start_timestamp: datetime
    end_timestamp: datetime

    def __post_init__(self) -> None:
        """Require timezone-aware, non-descending window timestamps."""
        _require_timezone_aware(self.start_timestamp, "start_timestamp")
        _require_timezone_aware(self.end_timestamp, "end_timestamp")
        if self.end_timestamp < self.start_timestamp:
            raise ValueError("end_timestamp must not precede start_timestamp")


@dataclass(frozen=True, slots=True)
class OpeningRange:
    """Records observed canonical values and evidence for an opening range."""

    window: ORBWindow
    open: float
    high: float
    low: float
    close: float
    candles: tuple[Candle, ...]

    def __post_init__(self) -> None:
        """Require the observed high to be at least the observed low."""
        if self.high < self.low:
            raise ValueError("high must not be below low")


class ORBBehaviorKind(str, Enum):
    """Identifies the objective ORB behavior states supported by current facts."""

    NO_ESCAPE = "NO_ESCAPE"
    ESCAPE_WITH_RETURN = "ESCAPE_WITH_RETURN"
    ESCAPE_WITHOUT_RETURN = "ESCAPE_WITHOUT_RETURN"


@dataclass(frozen=True, slots=True)
class ORBBehavior:
    """Represents one immutable classification from existing ORB observations."""

    kind: ORBBehaviorKind


class ORBEscapeDirection(str, Enum):
    """Identifies the ORB boundary crossed by an observed escape candle."""

    UPWARD = "UPWARD"
    DOWNWARD = "DOWNWARD"


@dataclass(frozen=True, slots=True)
class ORBEscapeEvent:
    """Records one observed canonical candle exiting an opening range boundary."""

    timestamp: datetime
    direction: ORBEscapeDirection
    candle: Candle
    boundary_crossed: float
    crossing_price: float

    def __post_init__(self) -> None:
        """Require a timestamp and crossing price consistent with the event facts."""
        _require_timezone_aware(self.timestamp, "timestamp")
        if self.timestamp != self.candle.timestamp:
            raise ValueError("timestamp must match the escape candle timestamp")
        if self.direction is ORBEscapeDirection.UPWARD:
            if self.crossing_price <= self.boundary_crossed:
                raise ValueError("upward crossing_price must exceed boundary_crossed")
        elif self.crossing_price >= self.boundary_crossed:
            raise ValueError("downward crossing_price must be below boundary_crossed")


@dataclass(frozen=True, slots=True)
class ORBPostEscapeObservation:
    """Records objective canonical price facts following an ORB escape event."""

    highest_price: float | None
    lowest_price: float | None
    maximum_favorable_excursion: float | None
    maximum_adverse_excursion: float | None
    returned_inside_range: bool
    first_return_inside_timestamp: datetime | None

    def __post_init__(self) -> None:
        """Keep return-state facts internally consistent and timezone-aware."""
        measurements = (
            self.highest_price,
            self.lowest_price,
            self.maximum_favorable_excursion,
            self.maximum_adverse_excursion,
        )
        if any(value is None for value in measurements) and not all(
            value is None for value in measurements
        ):
            raise ValueError("post-escape measurements must be all known or all unknown")
        if all(value is None for value in measurements) and self.returned_inside_range:
            raise ValueError("an unknown post-escape history cannot contain a range return")
        if self.highest_price is not None:
            if (
                self.lowest_price is None
                or self.maximum_favorable_excursion is None
                or self.maximum_adverse_excursion is None
            ):
                raise ValueError("post-escape measurements must be all known or all unknown")
            if self.highest_price < self.lowest_price:
                raise ValueError("highest_price must not be below lowest_price")
            if (
                self.maximum_favorable_excursion < 0
                or self.maximum_adverse_excursion < 0
            ):
                raise ValueError("post-escape excursions must be non-negative")
        if self.returned_inside_range != (self.first_return_inside_timestamp is not None):
            raise ValueError(
                "returned_inside_range must match first_return_inside_timestamp"
            )
        if self.first_return_inside_timestamp is not None:
            _require_timezone_aware(
                self.first_return_inside_timestamp,
                "first_return_inside_timestamp",
            )


@dataclass(frozen=True, slots=True)
class ORBSession:
    """Associates one canonical session with its observed opening range."""

    session: Session
    opening_range: OpeningRange


def _require_timezone_aware(timestamp: datetime, field_name: str) -> None:
    """Reject timestamps that cannot identify a canonical timezone instant."""
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
