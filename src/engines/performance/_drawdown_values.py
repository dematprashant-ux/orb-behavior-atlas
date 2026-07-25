"""Shared absolute-drawdown calculation over already-selected equity values."""

__all__ = ["calculate_absolute_drawdowns"]


def calculate_absolute_drawdowns(
    equity_values: tuple[float, ...],
) -> tuple[tuple[float, float], ...]:
    """Return ordered ``(running_peak, drawdown)`` pairs from zero.

    Callers retain ownership of their domain-specific equity-point and
    drawdown-result models. This helper only reuses the existing deterministic
    absolute-drawdown mathematics.
    """
    running_peak = 0.0
    values: list[tuple[float, float]] = []
    for equity_value in equity_values:
        running_peak = max(running_peak, equity_value)
        values.append((running_peak, running_peak - equity_value))
    return tuple(values)
