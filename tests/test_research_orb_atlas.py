"""Contract tests for the immutable in-memory ORB behavior atlas."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime
from unittest import TestCase
from zoneinfo import ZoneInfo

from src.engines.data.models import Candle, Instrument, Timeframe
from src.engines.research import (
    OpeningRange,
    ORBBehavior,
    ORBBehaviorAtlas,
    ORBBehaviorKind,
    ORBEscapeDirection,
    ORBEscapeEvent,
    ORBFeatures,
    ORBPostEscapeObservation,
    ORBWindow,
    build_behavior_atlas,
    build_behavior_record,
)


class ORBBehaviorAtlasTests(TestCase):
    """Verify atlas construction is ordered, immutable, and analysis-free."""

    def test_builds_an_empty_atlas(self) -> None:
        """Represent no completed records as an immutable empty collection."""
        atlas = build_behavior_atlas(())

        self.assertIsInstance(atlas, ORBBehaviorAtlas)
        self.assertEqual(len(atlas), 0)
        self.assertEqual(tuple(atlas), ())

    def test_builds_a_single_record_atlas(self) -> None:
        """Retain the exact record object for indexed and iterative access."""
        record = _record(high=106.0)

        atlas = build_behavior_atlas((record,))

        self.assertEqual(len(atlas), 1)
        self.assertIs(atlas[0], record)
        self.assertEqual(tuple(atlas), (record,))

    def test_preserves_multiple_record_order_deterministically(self) -> None:
        """Keep caller-supplied collection order without sorting or filtering."""
        first = _record(high=106.0)
        second = _record(high=108.0)

        atlas = build_behavior_atlas((second, first))

        self.assertEqual(tuple(atlas), (second, first))
        self.assertIs(atlas[1], first)

    def test_rejects_duplicate_records_by_existing_value_equality(self) -> None:
        """Reject separate but equal immutable records as canonical duplicates."""
        first = _record(high=106.0)
        equal_record = _record(high=106.0)

        with self.assertRaisesRegex(ValueError, "duplicate"):
            build_behavior_atlas((first, equal_record))

    def test_atlas_is_deterministic_and_immutable(self) -> None:
        """Return equal frozen atlas values without mutable collection state."""
        record = _record(high=106.0)
        first = build_behavior_atlas((record,))
        second = build_behavior_atlas((record,))

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.records = ()

    def test_rejects_malformed_collections(self) -> None:
        """Require a sequence containing only completed behavior records."""
        with self.assertRaises(TypeError):
            build_behavior_atlas(None)
        with self.assertRaises(TypeError):
            build_behavior_atlas((_record(high=106.0), object()))

    def test_factory_has_only_collection_and_model_dependencies(self) -> None:
        """Keep atlas construction independent from analysis and infrastructure."""
        with open("src/engines/research/orb/atlas.py", encoding="utf-8") as source_file:
            tree = ast.parse(source_file.read())

        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(
            imported_modules,
            {"collections.abc", "src.engines.research.orb.models"},
        )

    def test_queries_empty_atlas_to_empty_immutable_atlases(self) -> None:
        """Return new empty immutable atlases for every supported empty query."""
        atlas = build_behavior_atlas(())

        self.assertEqual(tuple(atlas.by_behavior(ORBBehaviorKind.NO_ESCAPE)), ())
        self.assertEqual(
            tuple(atlas.by_escape_direction(ORBEscapeDirection.UPWARD)),
            (),
        )
        self.assertEqual(tuple(atlas.by_return_to_range(True)), ())

    def test_queries_return_existing_matching_records_in_source_order(self) -> None:
        """Filter existing record facts without copying, sorting, or deriving values."""
        no_escape = _record(high=106.0)
        upward_return = _escape_record(
            high=108.0,
            direction=ORBEscapeDirection.UPWARD,
            returned=True,
        )
        downward_no_return = _escape_record(
            high=110.0,
            direction=ORBEscapeDirection.DOWNWARD,
            returned=False,
        )
        upward_no_return = _escape_record(
            high=112.0,
            direction=ORBEscapeDirection.UPWARD,
            returned=False,
        )
        atlas = build_behavior_atlas(
            (upward_return, no_escape, downward_no_return, upward_no_return)
        )

        self.assertEqual(
            tuple(atlas.by_behavior(ORBBehaviorKind.ESCAPE_WITHOUT_RETURN)),
            (downward_no_return, upward_no_return),
        )
        upward = atlas.by_escape_direction(ORBEscapeDirection.UPWARD)
        self.assertEqual(tuple(upward), (upward_return, upward_no_return))
        self.assertIs(upward[0], upward_return)
        self.assertEqual(
            tuple(atlas.by_return_to_range(False)),
            (downward_no_return, upward_no_return),
        )

    def test_queries_support_deterministic_chaining_without_duplicates(self) -> None:
        """Compose filters while preserving matching source references and order."""
        upward_return = _escape_record(
            high=108.0,
            direction=ORBEscapeDirection.UPWARD,
            returned=True,
        )
        upward_no_return = _escape_record(
            high=110.0,
            direction=ORBEscapeDirection.UPWARD,
            returned=False,
        )
        atlas = build_behavior_atlas((upward_no_return, upward_return))

        result = (
            atlas.by_escape_direction(ORBEscapeDirection.UPWARD)
            .by_return_to_range(True)
            .by_behavior(ORBBehaviorKind.ESCAPE_WITH_RETURN)
        )

        self.assertEqual(tuple(result), (upward_return,))
        self.assertIs(result[0], upward_return)
        self.assertIsNot(result, atlas)
        with self.assertRaises(FrozenInstanceError):
            result.records = ()

    def test_queries_return_empty_atlas_when_no_records_match(self) -> None:
        """Represent no matches with a new immutable empty atlas."""
        atlas = build_behavior_atlas((_record(high=106.0),))

        result = atlas.by_escape_direction(ORBEscapeDirection.DOWNWARD)

        self.assertIsInstance(result, ORBBehaviorAtlas)
        self.assertEqual(tuple(result), ())
        self.assertIsNot(result, atlas)

    def test_queries_reject_intrinsically_invalid_arguments(self) -> None:
        """Require stable enum and boolean query values without coercion."""
        atlas = build_behavior_atlas(())

        with self.assertRaises(TypeError):
            atlas.by_behavior("NO_ESCAPE")
        with self.assertRaises(TypeError):
            atlas.by_escape_direction("UPWARD")
        with self.assertRaises(TypeError):
            atlas.by_return_to_range(1)


def _record(*, high: float):
    """Build one complete immutable no-escape record for atlas tests."""
    candle = Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=_timestamp(9, 15),
        session_date=date(2026, 7, 17),
        open=100.0,
        high=high,
        low=98.0,
        close=104.0,
        volume=1,
    )
    opening_range = OpeningRange(
        window=ORBWindow(candle.timestamp, _timestamp(9, 30)),
        open=100.0,
        high=high,
        low=98.0,
        close=104.0,
        candles=(candle,),
    )
    behavior = ORBBehavior(ORBBehaviorKind.NO_ESCAPE)
    features = ORBFeatures(
        behavior=ORBBehaviorKind.NO_ESCAPE,
        escape_exists=False,
        escape_direction=None,
        returned_to_range=None,
        mfe=None,
        mae=None,
        range_size=high - 98.0,
    )
    return build_behavior_record(opening_range, None, None, behavior, features)


def _timestamp(hour: int, minute: int) -> datetime:
    """Return a canonical Asia/Kolkata timestamp for immutable test objects."""
    return datetime(2026, 7, 17, hour, minute, tzinfo=ZoneInfo("Asia/Kolkata"))


def _escape_record(
    *,
    high: float,
    direction: ORBEscapeDirection,
    returned: bool,
):
    """Build a complete record with existing escape and return facts for queries."""
    opening_candle = Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=_timestamp(9, 15),
        session_date=date(2026, 7, 17),
        open=100.0,
        high=high,
        low=98.0,
        close=104.0,
        volume=1,
    )
    opening_range = OpeningRange(
        window=ORBWindow(opening_candle.timestamp, _timestamp(9, 30)),
        open=100.0,
        high=high,
        low=98.0,
        close=104.0,
        candles=(opening_candle,),
    )
    boundary = high if direction is ORBEscapeDirection.UPWARD else 98.0
    escape_candle = Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=_timestamp(9, 30),
        session_date=date(2026, 7, 17),
        open=boundary,
        high=boundary + 1.0 if direction is ORBEscapeDirection.UPWARD else boundary,
        low=boundary if direction is ORBEscapeDirection.UPWARD else boundary - 1.0,
        close=boundary,
        volume=1,
    )
    escape_event = ORBEscapeEvent(
        timestamp=escape_candle.timestamp,
        direction=direction,
        candle=escape_candle,
        boundary_crossed=boundary,
        crossing_price=(
            escape_candle.high
            if direction is ORBEscapeDirection.UPWARD
            else escape_candle.low
        ),
    )
    favorable_excursion, adverse_excursion = (
        (2.0, 1.0)
        if direction is ORBEscapeDirection.UPWARD
        else (1.0, 2.0)
    )
    observation = ORBPostEscapeObservation(
        highest_price=boundary + 2.0,
        lowest_price=boundary - 1.0,
        maximum_favorable_excursion=favorable_excursion,
        maximum_adverse_excursion=adverse_excursion,
        returned_inside_range=returned,
        first_return_inside_timestamp=_timestamp(9, 35) if returned else None,
    )
    behavior_kind = (
        ORBBehaviorKind.ESCAPE_WITH_RETURN
        if returned
        else ORBBehaviorKind.ESCAPE_WITHOUT_RETURN
    )
    behavior = ORBBehavior(behavior_kind)
    features = ORBFeatures(
        behavior=behavior_kind,
        escape_exists=True,
        escape_direction=direction,
        returned_to_range=returned,
        mfe=favorable_excursion,
        mae=adverse_excursion,
        range_size=high - 98.0,
    )
    return build_behavior_record(
        opening_range,
        escape_event,
        observation,
        behavior,
        features,
    )
