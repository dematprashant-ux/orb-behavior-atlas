"""Batch-level canonical timestamp validation."""

from collections.abc import Sequence

from src.engines.data.models import Candle
from src.engines.data.validation._candle import validate_candle
from src.engines.data.validation._issues import build_issue
from src.engines.data.validation._models import CandleValidationResult, ValidationIssue
from src.engines.data.validation._rules import (
    duplicate_timestamp_finding,
    timestamp_order_finding,
)


def validate_candles(
    candles: Sequence[Candle],
    *,
    check_duplicates: bool = True,
    check_timestamp_order: bool = True,
) -> tuple[CandleValidationResult, ...]:
    """Validate candles without changing their order or canonical timestamps.

    Duplicate and ordering rules operate only on canonical ``Candle.timestamp``
    values produced by normalization. Provider-native timestamps are never
    inspected by this boundary.
    """
    if not isinstance(candles, Sequence):
        raise TypeError("candles must be a Sequence of Candle instances")
    if not isinstance(check_duplicates, bool):
        raise TypeError("check_duplicates must be a bool")
    if not isinstance(check_timestamp_order, bool):
        raise TypeError("check_timestamp_order must be a bool")

    results = [validate_candle(candle) for candle in candles]
    issues = [list(result.issues) for result in results]
    first_indices: dict[tuple[object, object, object], int] = {}
    prior_indices: dict[tuple[object, object], int] = {}

    for index, candle in enumerate(candles):
        duplicate_key = (candle.instrument, candle.timeframe, candle.timestamp)
        stream_key = (candle.instrument, candle.timeframe)

        if check_duplicates:
            first_index = first_indices.setdefault(duplicate_key, index)
            if first_index != index:
                issues[index].append(
                    build_issue(duplicate_timestamp_finding(related_index=first_index))
                )

        if check_timestamp_order and stream_key in prior_indices:
            prior_index = prior_indices[stream_key]
            if candle.timestamp < candles[prior_index].timestamp:
                issues[index].append(
                    build_issue(timestamp_order_finding(related_index=prior_index))
                )
        prior_indices[stream_key] = index

    return tuple(
        CandleValidationResult(candle=result.candle, issues=tuple(issues[index]))
        for index, result in enumerate(results)
    )
