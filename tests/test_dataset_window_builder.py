"""Contract tests for pure canonical-candle dataset range selection."""

from datetime import date, datetime, timedelta, timezone
from unittest import TestCase

from src.engines.backtesting.walk_forward import (
    DatasetWindowBuilder,
    DateTimeRange,
    StandardDatasetWindowBuilder,
)
from src.engines.data.models import Candle, Instrument, Timeframe


class DatasetWindowBuilderTests(TestCase):
    """Verify half-open slicing without data transformation or reordering."""

    def test_selects_half_open_range_in_order_and_allows_empty_windows(self) -> None:
        """Include the start boundary, exclude end, and retain candle references."""
        candles = (_candle(0), _candle(5), _candle(10))
        builder: DatasetWindowBuilder = StandardDatasetWindowBuilder()
        window = builder.build(candles, DateTimeRange(_time(5), _time(10)))
        self.assertEqual(window.observations, (_candle(5),))
        self.assertIs(window.observations[0], candles[1])
        self.assertEqual(
            builder.build((), DateTimeRange(_time(0), _time(5))).observations,
            (),
        )
        self.assertEqual(
            builder.build(candles, DateTimeRange(_time(20), _time(25))).observations,
            (),
        )

    def test_rejects_unordered_input_and_preserves_duplicate_timestamp_order(
        self,
    ) -> None:
        """Reject decreasing data while preserving valid duplicate timestamps."""
        builder = StandardDatasetWindowBuilder()
        duplicates = (_candle(5), _candle(5), _candle(10))
        self.assertEqual(
            len(
                builder.build(
                    duplicates,
                    DateTimeRange(_time(0), _time(10)),
                ).observations
            ),
            2,
        )
        with self.assertRaises(ValueError):
            builder.build(
                (_candle(5), _candle(0)),
                DateTimeRange(_time(0), _time(10)),
            )

    def test_rejects_boundary_misuse_without_mutating_inputs(self) -> None:
        """Require canonical tuple and range boundary types only."""
        builder = StandardDatasetWindowBuilder()
        with self.assertRaises(TypeError):
            builder.build([], DateTimeRange(_time(0), _time(5)))
        with self.assertRaises(TypeError):
            builder.build(
                (),
                object(),
            )


def _candle(minutes: int) -> Candle:
    """Build one valid canonical candle fixture with an aware timestamp."""
    return Candle(
        Instrument.BANKNIFTY,
        Timeframe.M5,
        _time(minutes),
        date(2026, 1, 1),
        1.0,
        1.0,
        1.0,
        1.0,
        0,
    )


def _time(minutes: int) -> datetime:
    """Return deterministic five-minute compatible timestamps."""
    return datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc) + timedelta(minutes=minutes)
