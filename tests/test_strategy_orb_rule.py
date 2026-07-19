"""Contract tests for the deterministic non-executing ORB rule strategy."""

import ast
from dataclasses import FrozenInstanceError
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
    build_behavior_atlas,
    build_behavior_record,
)
from src.engines.strategy import (
    ORBRuleStrategy,
    Strategy,
    StrategyDecisionType,
    build_strategy_context,
)


class ORBRuleStrategyTests(TestCase):
    """Verify documented structural decisions use existing research facts only."""

    def test_no_escape_and_escape_with_return_produce_no_action(self) -> None:
        """Map both documented non-setup behaviors to the structural no-action state."""
        strategy = ORBRuleStrategy()

        no_escape = strategy.evaluate(_context(_record_no_escape()))
        with_return = strategy.evaluate(
            _context(
                _record_escape(
                    direction=ORBEscapeDirection.UPWARD,
                    returned=True,
                )
            )
        )

        self.assertIs(no_escape.decision_type, StrategyDecisionType.NO_ACTION)
        self.assertIs(with_return.decision_type, StrategyDecisionType.NO_ACTION)

    def test_upward_escape_without_return_produces_long_setup(self) -> None:
        """Map only the existing upward escape direction to LONG_SETUP."""
        decision = ORBRuleStrategy().evaluate(
            _context(
                _record_escape(
                    direction=ORBEscapeDirection.UPWARD,
                    returned=False,
                )
            )
        )

        self.assertIs(decision.decision_type, StrategyDecisionType.LONG_SETUP)

    def test_downward_escape_without_return_produces_short_setup(self) -> None:
        """Map only the existing downward escape direction to SHORT_SETUP."""
        decision = ORBRuleStrategy().evaluate(
            _context(
                _record_escape(
                    direction=ORBEscapeDirection.DOWNWARD,
                    returned=False,
                )
            )
        )

        self.assertIs(decision.decision_type, StrategyDecisionType.SHORT_SETUP)

    def test_evaluation_is_deterministic_and_output_is_immutable(self) -> None:
        """Return equal frozen decisions that retain the exact context reference."""
        context = _context(
            _record_escape(
                direction=ORBEscapeDirection.UPWARD,
                returned=False,
            )
        )
        strategy: Strategy = ORBRuleStrategy()

        first = strategy.evaluate(context)
        second = strategy.evaluate(context)

        self.assertEqual(first, second)
        self.assertIs(first.context, context)
        with self.assertRaises(FrozenInstanceError):
            first.decision_type = StrategyDecisionType.NO_ACTION

    def test_evaluation_rejects_intrinsically_invalid_context(self) -> None:
        """Require the immutable StrategyContext boundary without coercion."""
        with self.assertRaises(TypeError):
            ORBRuleStrategy().evaluate(object())

    def test_strategy_imports_only_strategy_and_research_model_boundaries(self) -> None:
        """Keep rule evaluation independent from candles, I/O, and execution."""
        with open("src/engines/strategy/orb_rule.py", encoding="utf-8") as source_file:
            tree = ast.parse(source_file.read())

        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(
            imported_modules,
            {
                "src.engines.research.orb.models",
                "src.engines.strategy.models",
            },
        )


def _context(record):
    """Build a context retaining one existing completed record in its atlas."""
    return build_strategy_context(record, build_behavior_atlas((record,)))


def _record_no_escape():
    """Build one completed no-escape record from existing immutable research types."""
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
    return build_behavior_record(opening_range, None, None, behavior, features)


def _record_escape(*, direction: ORBEscapeDirection, returned: bool):
    """Build one existing escaped record without recalculating its facts."""
    opening_range = _opening_range()
    boundary = (
        opening_range.high
        if direction is ORBEscapeDirection.UPWARD
        else opening_range.low
    )
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
    favorable, adverse = (
        (2.0, 1.0)
        if direction is ORBEscapeDirection.UPWARD
        else (1.0, 2.0)
    )
    observation = ORBPostEscapeObservation(
        highest_price=boundary + 2.0,
        lowest_price=boundary - 1.0,
        maximum_favorable_excursion=favorable,
        maximum_adverse_excursion=adverse,
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
        mfe=favorable,
        mae=adverse,
        range_size=8.0,
    )
    return build_behavior_record(
        opening_range,
        escape_event,
        observation,
        behavior,
        features,
    )


def _opening_range() -> OpeningRange:
    """Build existing opening-range facts required by completed record fixtures."""
    candle = Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=_timestamp(9, 15),
        session_date=date(2026, 7, 17),
        open=100.0,
        high=106.0,
        low=98.0,
        close=104.0,
        volume=1,
    )
    return OpeningRange(
        window=ORBWindow(candle.timestamp, _timestamp(9, 30)),
        open=100.0,
        high=106.0,
        low=98.0,
        close=104.0,
        candles=(candle,),
    )


def _timestamp(hour: int, minute: int) -> datetime:
    """Return a canonical Asia/Kolkata timestamp for immutable test evidence."""
    return datetime(2026, 7, 17, hour, minute, tzinfo=ZoneInfo("Asia/Kolkata"))
