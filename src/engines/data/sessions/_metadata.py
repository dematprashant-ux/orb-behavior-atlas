"""Immutable metadata supplied during session construction."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SessionMetadata:
    """Tri-state facts about a trading session.

    ``None`` means the fact has not been determined. Session construction never
    infers expiry or holiday information.
    """

    is_weekly_expiry: bool | None = None
    is_monthly_expiry: bool | None = None
    has_holiday_gap: bool | None = None

    def __post_init__(self) -> None:
        """Reject values outside the tri-state metadata contract."""
        for value in (
            self.is_weekly_expiry,
            self.is_monthly_expiry,
            self.has_holiday_gap,
        ):
            if value is not None and not isinstance(value, bool):
                raise TypeError("Session metadata values must be bool or None.")
