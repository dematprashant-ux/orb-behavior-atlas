"""Contract tests for canonical aggregate ORB behavior records."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime
from unittest import TestCase
from zoneinfo import ZoneInfo

from src.engines.data.models import Candle, Instrument, Timeframe
from src.engines.research import (
    OpeningRange,
    ORBBehavior,
    ORBBehaviorKind,
    ORBBehaviorRecord,
    ORBEscapeDirection,
    ORBEscapeEvent,
    ORBFeatures,
    ORBPostEscapeObservation,
    ORBWindow,
    build_behavior_record,
)


class ORBBehaviorRecordTests(TestCase):
    """Verify aggregation preserves supplied immutable research outputs."""

    def test_builds_a_complete_escape_record(self) -> None:
        """Retain exact child-object references without recomputing their facts."""
        opening_range, escape_event, observation, behavior, features = _escape_inputs()

        record = build_behavior_record(
            opening_range,
            escape_event,
            observation,
            behavior,
            features,
        )

        self.assertIsInstance(record, ORBBehaviorRecord)
        self.assertIs(record.opening_range, opening_range)
        self.assertIs(record.escape_event, escape_event)
        self.assertIs(record.post_escape_observation, observation)
        self.assertIs(record.behavior, behavior)
        self.assertIs(record.features, features)

    def test_builds_a_no_escape_record(self) -> None:
        """Represent absent optional outputs without fabricating child objects."""
        opening_range = _opening_range()
        behavior = ORBBehavior(ORBBehaviorKind.NO_ESCAPE)
        features = ORBFeatures(
            behavior=ORBBehaviorKind.NO_ESCAPE,
            escape_exists=False,
            escape_direction=None,
            returned_to_range=None,
            mfe=None,
            mae=None,
            range_size=8.0,
        )

        record = build_behavior_record(opening_range, None, None, behavior, features)

        self.assertIsNone(record.escape_event)
        self.assertIsNone(record.post_escape_observation)
        self.assertIs(record.behavior.kind, ORBBehaviorKind.NO_ESCAPE)

    def test_construction_is_deterministic_and_record_is_immutable(self) -> None:
        """Return equal frozen aggregate records for the same child values."""
        first = build_behavior_record(*_escape_inputs())
        second = build_behavior_record(*_escape_inputs())

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.behavior = ORBBehavior(ORBBehaviorKind.NO_ESCAPE)

    def test_rejects_mismatched_escape_boundary_and_range(self) -> None:
        """Reject an escape child object whose boundary conflicts with the range."""
        opening_range, escape_event, observation, behavior, features = _escape_inputs()
        mismatched_event = ORBEscapeEvent(
            timestamp=escape_event.timestamp,
            direction=escape_event.direction,
            candle=escape_event.candle,
            boundary_crossed=105.0,
            crossing_price=107.0,
        )

        with self.assertRaisesRegex(ValueError, "boundary does not match"):
            build_behavior_record(
                opening_range,
                mismatched_event,
                observation,
                behavior,
                features,
            )

    def test_rejects_mismatched_features_and_observation(self) -> None:
        """Reject a feature child object that overrides an observed MFE value."""
        opening_range, escape_event, observation, behavior, _ = _escape_inputs()
        mismatched_features = ORBFeatures(
            behavior=ORBBehaviorKind.ESCAPE_WITH_RETURN,
            escape_exists=True,
            escape_direction=ORBEscapeDirection.UPWARD,
            returned_to_range=True,
            mfe=5.0,
            mae=2.0,
            range_size=8.0,
        )

        with self.assertRaisesRegex(ValueError, "observation and features"):
            build_behavior_record(
                opening_range,
                escape_event,
                observation,
                behavior,
                mismatched_features,
            )

    def test_factory_imports_only_orb_model_types(self) -> None:
        """Keep aggregation independent from analysis and infrastructure layers."""
        with open("src/engines/research/orb/record.py", encoding="utf-8") as source_file:
            tree = ast.parse(source_file.read())

        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(imported_modules, {"src.engines.research.orb.models"})


def _escape_inputs() -> tuple[
    OpeningRange,
    ORBEscapeEvent,
    ORBPostEscapeObservation,
    ORBBehavior,
    ORBFeatures,
]:
    """Create mutually consistent immutable outputs from prior milestones."""
    opening_range = _opening_range()
    escape_candle = _candle(hour=9, minute=30, high=107.0, low=103.0, close=106.0)
    escape_event = ORBEscapeEvent(
        timestamp=escape_candle.timestamp,
        direction=ORBEscapeDirection.UPWARD,
        candle=escape_candle,
        boundary_crossed=106.0,
        crossing_price=107.0,
    )
    observation = ORBPostEscapeObservation(
        highest_price=110.0,
        lowest_price=104.0,
        maximum_favorable_excursion=4.0,
        maximum_adverse_excursion=2.0,
        returned_inside_range=True,
        first_return_inside_timestamp=_timestamp(9, 35),
    )
    behavior = ORBBehavior(ORBBehaviorKind.ESCAPE_WITH_RETURN)
    features = ORBFeatures(
        behavior=ORBBehaviorKind.ESCAPE_WITH_RETURN,
        escape_exists=True,
        escape_direction=ORBEscapeDirection.UPWARD,
        returned_to_range=True,
        mfe=4.0,
        mae=2.0,
        range_size=8.0,
    )
    return opening_range, escape_event, observation, behavior, features


def _opening_range() -> OpeningRange:
    """Create one existing immutable opening-range output for aggregation tests."""
    candle = _candle()
    return OpeningRange(
        window=ORBWindow(candle.timestamp, _timestamp(9, 30)),
        open=100.0,
        high=106.0,
        low=98.0,
        close=104.0,
        candles=(candle,),
    )


def _candle(
    *,
    hour: int = 9,
    minute: int = 15,
    high: float = 102.0,
    low: float = 99.0,
    close: float = 101.0,
) -> Candle:
    """Create immutable canonical candle evidence for building test inputs."""
    return Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=_timestamp(hour, minute),
        session_date=date(2026, 7, 17),
        open=100.0,
        high=high,
        low=low,
        close=close,
        volume=1,
    )


def _timestamp(hour: int, minute: int) -> datetime:
    """Return an Asia/Kolkata timestamp for immutable test objects."""
    return datetime(2026, 7, 17, hour, minute, tzinfo=ZoneInfo("Asia/Kolkata"))
