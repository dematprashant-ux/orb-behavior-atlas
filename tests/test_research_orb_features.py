"""Contract tests for standardized ORB feature generation."""

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
    ORBEscapeDirection,
    ORBEscapeEvent,
    ORBFeatures,
    ORBPostEscapeObservation,
    ORBWindow,
    generate_orb_features,
)


class ORBFeatureGenerationTests(TestCase):
    """Verify features project existing research outputs without data access."""

    def test_generates_complete_no_escape_features(self) -> None:
        """Represent absent escape facts explicitly without fabricating observations."""
        features = generate_orb_features(
            _opening_range(),
            None,
            None,
            ORBBehavior(ORBBehaviorKind.NO_ESCAPE),
        )

        self.assertIsInstance(features, ORBFeatures)
        self.assertIs(features.behavior, ORBBehaviorKind.NO_ESCAPE)
        self.assertFalse(features.escape_exists)
        self.assertIsNone(features.escape_direction)
        self.assertIsNone(features.returned_to_range)
        self.assertIsNone(features.mfe)
        self.assertIsNone(features.mae)
        self.assertEqual(features.range_size, 8.0)

    def test_generates_escape_with_return_features(self) -> None:
        """Project existing escape direction and observation values unchanged."""
        features = generate_orb_features(
            _opening_range(),
            _escape_event(),
            _observation(returned_inside_range=True),
            ORBBehavior(ORBBehaviorKind.ESCAPE_WITH_RETURN),
        )

        self.assertTrue(features.escape_exists)
        self.assertIs(features.escape_direction, ORBEscapeDirection.UPWARD)
        self.assertTrue(features.returned_to_range)
        self.assertEqual(features.mfe, 4.0)
        self.assertEqual(features.mae, 2.0)

    def test_generates_escape_without_return_features(self) -> None:
        """Preserve the supplied no-return fact without outcome inference."""
        features = generate_orb_features(
            _opening_range(),
            _escape_event(),
            _observation(returned_inside_range=False),
            ORBBehavior(ORBBehaviorKind.ESCAPE_WITHOUT_RETURN),
        )

        self.assertIs(features.behavior, ORBBehaviorKind.ESCAPE_WITHOUT_RETURN)
        self.assertFalse(features.returned_to_range)

    def test_generation_is_deterministic_and_features_are_immutable(self) -> None:
        """Return equal slotted feature values for equal supplied inputs."""
        inputs = (
            _opening_range(),
            _escape_event(),
            _observation(returned_inside_range=False),
            ORBBehavior(ORBBehaviorKind.ESCAPE_WITHOUT_RETURN),
        )

        first = generate_orb_features(*inputs)
        second = generate_orb_features(*inputs)

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.range_size = 0.0

    def test_rejects_behavior_that_disagrees_with_existing_observation(self) -> None:
        """Prevent a feature record from silently overriding classification facts."""
        with self.assertRaisesRegex(ValueError, "must match"):
            generate_orb_features(
                _opening_range(),
                _escape_event(),
                _observation(returned_inside_range=True),
                ORBBehavior(ORBBehaviorKind.ESCAPE_WITHOUT_RETURN),
            )

    def test_generator_imports_only_orb_model_types(self) -> None:
        """Keep feature projection free from market-data and infrastructure layers."""
        with open("src/engines/research/orb/features.py", encoding="utf-8") as source_file:
            tree = ast.parse(source_file.read())

        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(imported_modules, {"src.engines.research.orb.models"})


def _opening_range() -> OpeningRange:
    """Create immutable opening-range context with a directly known range size."""
    first_candle = _candle()
    return OpeningRange(
        window=ORBWindow(
            start_timestamp=first_candle.timestamp,
            end_timestamp=_timestamp(9, 30),
        ),
        open=100.0,
        high=106.0,
        low=98.0,
        close=104.0,
        candles=(first_candle,),
    )


def _escape_event() -> ORBEscapeEvent:
    """Create an existing upward escape event without feature-side extraction."""
    candle = _candle(hour=9, minute=30, high=107.0, low=103.0, close=106.0)
    return ORBEscapeEvent(
        timestamp=candle.timestamp,
        direction=ORBEscapeDirection.UPWARD,
        candle=candle,
        boundary_crossed=106.0,
        crossing_price=107.0,
    )


def _observation(*, returned_inside_range: bool) -> ORBPostEscapeObservation:
    """Create an existing post-escape observation for pure feature projection."""
    return ORBPostEscapeObservation(
        highest_price=110.0,
        lowest_price=104.0,
        maximum_favorable_excursion=4.0,
        maximum_adverse_excursion=2.0,
        returned_inside_range=returned_inside_range,
        first_return_inside_timestamp=(
            _timestamp(9, 35) if returned_inside_range else None
        ),
    )


def _candle(
    *,
    hour: int = 9,
    minute: int = 15,
    high: float = 102.0,
    low: float = 99.0,
    close: float = 101.0,
) -> Candle:
    """Create canonical evidence used only to construct immutable test inputs."""
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
    """Return a canonical Asia/Kolkata timestamp for immutable test objects."""
    return datetime(2026, 7, 17, hour, minute, tzinfo=ZoneInfo("Asia/Kolkata"))
