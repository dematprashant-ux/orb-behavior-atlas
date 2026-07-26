"""Contract tests for deterministic descriptive statistics over ORB atlases."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime
from unittest import TestCase
from zoneinfo import ZoneInfo

from src.engines.data.models import Candle, Instrument, Timeframe
from src.engines.research import (
    OpeningRange,
    ORBBehavior,
    ORBBehaviorDescriptiveStatistics,
    ORBBehaviorKind,
    ORBEscapeDirection,
    ORBEscapeEvent,
    ORBFeatures,
    ORBFeatureSummary,
    ORBPostEscapeObservation,
    ORBWindow,
    build_behavior_atlas,
    build_behavior_record,
    compute_behavior_descriptive_statistics,
    compute_behavior_statistics,
)


class ORBBehaviorDescriptiveStatisticsTests(TestCase):
    """Verify descriptive summaries compose existing immutable ORB facts."""

    def test_empty_atlas_has_empty_categories_and_numeric_samples(self) -> None:
        """Represent no completed records without inventing values or groups."""
        result = compute_behavior_descriptive_statistics(build_behavior_atlas(()))

        self.assertIsInstance(result, ORBBehaviorDescriptiveStatistics)
        self.assertEqual(result.categorical_counts.total_records, 0)
        self.assertEqual(dict(result.behavior_proportions), {})
        self.assertEqual(dict(result.escape_direction_proportions), {})
        self.assertEqual(dict(result.return_to_range_proportions), {})
        self.assertEqual(
            result.range_size,
            ORBFeatureSummary(0, None, None, None, None),
        )
        self.assertEqual(
            result.maximum_favorable_excursion,
            ORBFeatureSummary(0, None, None, None, None),
        )
        self.assertEqual(
            result.maximum_adverse_excursion,
            ORBFeatureSummary(0, None, None, None, None),
        )

    def test_single_record_preserves_existing_categorical_fact(self) -> None:
        """Summarize a no-escape record without manufacturing excursion values."""
        record = _no_escape_record(range_size=2.0)
        result = compute_behavior_descriptive_statistics(
            build_behavior_atlas((record,))
        )

        self.assertEqual(
            dict(result.behavior_proportions),
            {ORBBehaviorKind.NO_ESCAPE: 1.0},
        )
        self.assertEqual(dict(result.escape_direction_proportions), {})
        self.assertEqual(dict(result.return_to_range_proportions), {})
        self.assertEqual(result.range_size, ORBFeatureSummary(1, 2.0, 2.0, 2.0, 2.0))

    def test_mixed_records_produce_exact_counts_proportions_and_summaries(self) -> None:
        """Use only stored categories and features in their canonical order."""
        no_escape = _no_escape_record(range_size=2.0)
        upward_return = _escape_record(
            range_size=4.0,
            direction=ORBEscapeDirection.UPWARD,
            returned=True,
            mfe=1.0,
            mae=2.0,
        )
        downward_no_return = _escape_record(
            range_size=6.0,
            direction=ORBEscapeDirection.DOWNWARD,
            returned=False,
            mfe=3.0,
            mae=4.0,
        )
        upward_no_return = _escape_record(
            range_size=8.0,
            direction=ORBEscapeDirection.UPWARD,
            returned=False,
            mfe=5.0,
            mae=6.0,
        )
        atlas = build_behavior_atlas(
            (no_escape, upward_return, downward_no_return, upward_no_return)
        )

        result = compute_behavior_descriptive_statistics(atlas)

        self.assertEqual(result.categorical_counts.total_records, 4)
        self.assertEqual(
            dict(result.categorical_distributions.behavior_distribution),
            {
                ORBBehaviorKind.NO_ESCAPE: 1,
                ORBBehaviorKind.ESCAPE_WITH_RETURN: 1,
                ORBBehaviorKind.ESCAPE_WITHOUT_RETURN: 2,
            },
        )
        self.assertEqual(
            dict(result.behavior_proportions),
            {
                ORBBehaviorKind.NO_ESCAPE: 0.25,
                ORBBehaviorKind.ESCAPE_WITH_RETURN: 0.25,
                ORBBehaviorKind.ESCAPE_WITHOUT_RETURN: 0.5,
            },
        )
        self.assertEqual(
            dict(result.escape_direction_proportions),
            {
                ORBEscapeDirection.UPWARD: 2 / 3,
                ORBEscapeDirection.DOWNWARD: 1 / 3,
            },
        )
        self.assertEqual(
            dict(result.return_to_range_proportions),
            {True: 1 / 3, False: 2 / 3},
        )
        self.assertEqual(result.range_size, ORBFeatureSummary(4, 2.0, 8.0, 5.0, 5.0))
        self.assertEqual(
            result.maximum_favorable_excursion,
            ORBFeatureSummary(3, 1.0, 5.0, 3.0, 3.0),
        )
        self.assertEqual(
            result.maximum_adverse_excursion,
            ORBFeatureSummary(3, 2.0, 6.0, 4.0, 4.0),
        )

    def test_filtered_atlas_uses_existing_filtering_without_mutation(self) -> None:
        """Accept the existing query result as the sole filtered input boundary."""
        upward = _escape_record(
            range_size=3.0,
            direction=ORBEscapeDirection.UPWARD,
            returned=True,
            mfe=2.0,
            mae=1.0,
        )
        downward = _escape_record(
            range_size=7.0,
            direction=ORBEscapeDirection.DOWNWARD,
            returned=False,
            mfe=4.0,
            mae=3.0,
        )
        atlas = build_behavior_atlas((upward, downward))

        result = compute_behavior_descriptive_statistics(
            atlas.filter(escape_direction=ORBEscapeDirection.UPWARD)
        )

        self.assertEqual(result.categorical_counts.total_records, 1)
        self.assertEqual(result.range_size, ORBFeatureSummary(1, 3.0, 3.0, 3.0, 3.0))
        self.assertEqual(tuple(atlas), (upward, downward))

    def test_result_is_deterministic_immutable_and_mapping_backed(self) -> None:
        """Expose frozen value objects and read-only ordered proportion mappings."""
        atlas = build_behavior_atlas((_no_escape_record(range_size=2.0),))

        first = compute_behavior_descriptive_statistics(atlas)
        second = compute_behavior_descriptive_statistics(atlas)

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.range_size = ORBFeatureSummary(0, None, None, None, None)
        with self.assertRaises(TypeError):
            first.behavior_proportions[ORBBehaviorKind.NO_ESCAPE] = 0.0

    def test_rejects_invalid_input_and_non_finite_existing_feature_values(self) -> None:
        """Fail rather than silently normalize malformed source feature facts."""
        with self.assertRaises(TypeError):
            compute_behavior_descriptive_statistics(())

        record = _no_escape_record(range_size=2.0)
        object.__setattr__(record.features, "range_size", float("nan"))
        with self.assertRaisesRegex(ValueError, "finite"):
            compute_behavior_descriptive_statistics(build_behavior_atlas((record,)))

    def test_existing_count_statistics_remain_unchanged(self) -> None:
        """Leave the pre-existing count-only statistics capability untouched."""
        atlas = build_behavior_atlas((_no_escape_record(range_size=2.0),))

        self.assertEqual(compute_behavior_statistics(atlas).total_records, 1)


def _no_escape_record(*, range_size: float):
    """Build one complete no-escape record with an explicit existing range size."""
    opening_range = _opening_range(range_size)
    features = ORBFeatures(
        behavior=ORBBehaviorKind.NO_ESCAPE,
        escape_exists=False,
        escape_direction=None,
        returned_to_range=None,
        mfe=None,
        mae=None,
        range_size=range_size,
    )
    return build_behavior_record(
        opening_range,
        None,
        None,
        ORBBehavior(ORBBehaviorKind.NO_ESCAPE),
        features,
    )


def _escape_record(
    *,
    range_size: float,
    direction: ORBEscapeDirection,
    returned: bool,
    mfe: float,
    mae: float,
):
    """Build one complete existing escape record with explicit feature facts."""
    opening_range = _opening_range(range_size)
    boundary = (
        opening_range.high
        if direction is ORBEscapeDirection.UPWARD
        else opening_range.low
    )
    escape_candle = _candle(
        timestamp=_timestamp(9, 30),
        high=boundary + 1.0,
        low=boundary - 1.0,
    )
    crossing_price = (
        escape_candle.high
        if direction is ORBEscapeDirection.UPWARD
        else escape_candle.low
    )
    event = ORBEscapeEvent(
        timestamp=escape_candle.timestamp,
        direction=direction,
        candle=escape_candle,
        boundary_crossed=boundary,
        crossing_price=crossing_price,
    )
    observation = ORBPostEscapeObservation(
        highest_price=opening_range.high + mfe,
        lowest_price=opening_range.low - mae,
        maximum_favorable_excursion=mfe,
        maximum_adverse_excursion=mae,
        returned_inside_range=returned,
        first_return_inside_timestamp=_timestamp(9, 35) if returned else None,
    )
    behavior_kind = (
        ORBBehaviorKind.ESCAPE_WITH_RETURN
        if returned
        else ORBBehaviorKind.ESCAPE_WITHOUT_RETURN
    )
    features = ORBFeatures(
        behavior=behavior_kind,
        escape_exists=True,
        escape_direction=direction,
        returned_to_range=returned,
        mfe=mfe,
        mae=mae,
        range_size=range_size,
    )
    return build_behavior_record(
        opening_range,
        event,
        observation,
        ORBBehavior(behavior_kind),
        features,
    )


def _opening_range(range_size: float) -> OpeningRange:
    """Build canonical opening-range evidence for one deterministic test record."""
    candle = _candle(
        timestamp=_timestamp(9, 15),
        high=100.0 + range_size,
        low=100.0,
    )
    return OpeningRange(
        window=ORBWindow(candle.timestamp, _timestamp(9, 30)),
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        candles=(candle,),
    )


def _candle(*, timestamp: datetime, high: float, low: float) -> Candle:
    """Build one valid canonical M5 candle for deterministic research tests."""
    return Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=timestamp,
        session_date=date(2026, 7, 17),
        open=(high + low) / 2,
        high=high,
        low=low,
        close=(high + low) / 2,
        volume=1,
    )


def _timestamp(hour: int, minute: int) -> datetime:
    """Return a canonical Asia/Kolkata timestamp for immutable test facts."""
    return datetime(2026, 7, 17, hour, minute, tzinfo=ZoneInfo("Asia/Kolkata"))
