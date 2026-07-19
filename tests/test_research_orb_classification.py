"""Contract tests for pure ORB behavior classification from observations."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime, timedelta
import ast
from unittest import TestCase
from zoneinfo import ZoneInfo

from src.engines.data.models import Candle, Instrument, Session, Timeframe, Weekday
from src.engines.research import (
    ORBBehavior,
    ORBBehaviorKind,
    ORBEscapeEvent,
    ORBPostEscapeObservation,
    OpeningRange,
    classify_orb_behavior,
    extract_opening_range,
    find_first_escape_event,
)


class ORBBehaviorClassificationTests(TestCase):
    """Verify behavior labels are a narrow mapping over existing observations."""

    def test_classifies_no_escape_without_an_observation(self) -> None:
        """Represent a supplied absence of escape without looking at candles."""
        behavior = classify_orb_behavior(_opening_range(), None, None)

        self.assertIsInstance(behavior, ORBBehavior)
        self.assertIs(behavior.kind, ORBBehaviorKind.NO_ESCAPE)

    def test_classifies_escape_with_return(self) -> None:
        """Map the existing return observation to its objective behavior state."""
        behavior = classify_orb_behavior(
            _opening_range(),
            _escape_event(),
            _observation(returned_inside_range=True),
        )

        self.assertIs(behavior.kind, ORBBehaviorKind.ESCAPE_WITH_RETURN)

    def test_classifies_escape_without_return(self) -> None:
        """Map the existing no-return observation without deriving price facts."""
        behavior = classify_orb_behavior(
            _opening_range(),
            _escape_event(),
            _observation(returned_inside_range=False),
        )

        self.assertIs(behavior.kind, ORBBehaviorKind.ESCAPE_WITHOUT_RETURN)

    def test_classification_is_deterministic_and_behavior_is_immutable(self) -> None:
        """Return equal immutable values for equal input observations."""
        first = classify_orb_behavior(
            _opening_range(),
            _escape_event(),
            _observation(returned_inside_range=False),
        )
        second = classify_orb_behavior(
            _opening_range(),
            _escape_event(),
            _observation(returned_inside_range=False),
        )

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.kind = ORBBehaviorKind.NO_ESCAPE

    def test_rejects_an_impossible_optional_input_combination(self) -> None:
        """Avoid classifying post-escape facts when the escape is absent."""
        with self.assertRaisesRegex(ValueError, "requires an escape event"):
            classify_orb_behavior(
                _opening_range(),
                None,
                _observation(returned_inside_range=False),
            )

    def test_behavior_kind_values_are_stable(self) -> None:
        """Expose only categories supported by the current observation model."""
        self.assertEqual(
            tuple(ORBBehaviorKind),
            (
                ORBBehaviorKind.NO_ESCAPE,
                ORBBehaviorKind.ESCAPE_WITH_RETURN,
                ORBBehaviorKind.ESCAPE_WITHOUT_RETURN,
            ),
        )

    def test_classifier_has_no_market_data_or_infrastructure_dependencies(self) -> None:
        """Keep behavior mapping independent from candle and infrastructure layers."""
        with open(
            "src/engines/research/orb/classification.py",
            encoding="utf-8",
        ) as source_file:
            tree = ast.parse(source_file.read())

        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(imported_modules, {"src.engines.research.orb.models"})


def _opening_range() -> OpeningRange:
    """Create canonical range context without invoking the classifier on candles."""
    return extract_opening_range(_session(_range_candles()), duration=timedelta(minutes=15))


def _escape_event() -> ORBEscapeEvent:
    """Create an existing escape event for classification-only tests."""
    session = _session(
        _range_candles()
        + (_candle(9, 30, high=107.0, low=103.0, close=106.0),)
    )
    opening_range = extract_opening_range(session, duration=timedelta(minutes=15))
    escape_event = find_first_escape_event(opening_range, session)
    if escape_event is None:
        raise AssertionError("Expected the test session to produce an escape event.")
    return escape_event


def _observation(*, returned_inside_range: bool) -> ORBPostEscapeObservation:
    """Create existing factual observation input without performing classification."""
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


def _range_candles() -> tuple[Candle, ...]:
    """Create canonical range evidence with high 106 and low 98."""
    return (
        _candle(9, 15, open_price=100.0, high=102.0, low=99.0, close=101.0),
        _candle(9, 20, open_price=101.0, high=106.0, low=100.0, close=105.0),
        _candle(9, 25, open_price=105.0, high=105.0, low=98.0, close=104.0),
    )


def _session(candles: tuple[Candle, ...]) -> Session:
    """Create canonical session context used only to build test inputs."""
    return Session(
        session_date=date(2026, 7, 17),
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        weekday=Weekday.FRIDAY,
        is_weekly_expiry=None,
        is_monthly_expiry=None,
        has_holiday_gap=None,
        candles=candles,
    )


def _candle(
    hour: int,
    minute: int,
    *,
    open_price: float = 100.0,
    high: float = 102.0,
    low: float = 99.0,
    close: float = 101.0,
) -> Candle:
    """Create one canonical M5 candle for building immutable test inputs."""
    return Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=_timestamp(hour, minute),
        session_date=date(2026, 7, 17),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=1,
    )


def _timestamp(hour: int, minute: int) -> datetime:
    """Return a canonical Asia/Kolkata test timestamp."""
    return datetime(2026, 7, 17, hour, minute, tzinfo=ZoneInfo("Asia/Kolkata"))
