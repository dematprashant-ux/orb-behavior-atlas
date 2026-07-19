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
    ORBFeatures,
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
