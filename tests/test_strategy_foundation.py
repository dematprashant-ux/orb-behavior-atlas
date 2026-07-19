"""Contract tests for the structural Strategy Engine foundation."""

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
    ORBFeatures,
    ORBWindow,
    build_behavior_atlas,
    build_behavior_record,
)
from src.engines.strategy import (
    Strategy,
    StrategyContext,
    StrategyDecision,
    StrategyDecisionType,
    build_strategy_context,
)


class StrategyFoundationTests(TestCase):
    """Verify the strategy boundary is immutable, typed, and behavior-free."""

    def test_public_models_are_immutable_and_use_stable_enum_values(self) -> None:
        """Expose frozen value objects and structural decision labels only."""
        context = _context()
        decision = StrategyDecision(
            context=context,
            decision_type=StrategyDecisionType.NO_ACTION,
        )

        self.assertTrue(is_dataclass(context))
        self.assertTrue(is_dataclass(decision))
        self.assertFalse(hasattr(context, "__dict__"))
        self.assertFalse(hasattr(decision, "__dict__"))
        self.assertEqual(StrategyDecisionType.NO_ACTION.value, "NO_ACTION")
        self.assertEqual(StrategyDecisionType.LONG_SETUP.value, "LONG_SETUP")
        self.assertEqual(StrategyDecisionType.SHORT_SETUP.value, "SHORT_SETUP")
        with self.assertRaises(FrozenInstanceError):
            context.record = _record(high=108.0)
        with self.assertRaises(FrozenInstanceError):
            decision.decision_type = StrategyDecisionType.LONG_SETUP

    def test_context_builder_retains_existing_research_references(self) -> None:
        """Aggregate existing artifacts without duplicating their stored facts."""
        record = _record(high=106.0)
        atlas = build_behavior_atlas((record,))

        context = build_strategy_context(record, atlas)

        self.assertIsInstance(context, StrategyContext)
        self.assertIs(context.record, record)
        self.assertIs(context.atlas, atlas)
        self.assertEqual(context, build_strategy_context(record, atlas))

    def test_context_builder_rejects_intrinsic_misuse(self) -> None:
        """Require canonical research inputs and selected-record membership."""
        record = _record(high=106.0)
        atlas = build_behavior_atlas((_record(high=108.0),))

        with self.assertRaises(TypeError):
            build_strategy_context(object(), atlas)
        with self.assertRaises(TypeError):
            build_strategy_context(record, object())
        with self.assertRaisesRegex(ValueError, "present"):
            build_strategy_context(record, atlas)

    def test_decision_rejects_unsupported_structural_values(self) -> None:
        """Require a context and stable decision enum without inferring a signal."""
        with self.assertRaises(TypeError):
            StrategyDecision(
                context=object(),
                decision_type=StrategyDecisionType.NO_ACTION,
            )
        with self.assertRaises(TypeError):
            StrategyDecision(context=_context(), decision_type="NO_ACTION")

    def test_strategy_protocol_supports_a_pure_structural_implementation(self) -> None:
        """Confirm the protocol accepts a deterministic non-executing evaluator."""
        context = _context()
        decision = _evaluate_strategy(_NoActionStrategy(), context)

        self.assertEqual(decision.context, context)
        self.assertIs(decision.decision_type, StrategyDecisionType.NO_ACTION)

    def test_strategy_modules_depend_only_on_research_models_and_protocols(
        self,
    ) -> None:
        """Keep the foundation independent from providers, storage, and execution."""
        expected_imports = {
            "src/engines/strategy/context.py": {
                "src.engines.research.orb.models",
                "src.engines.strategy.models",
            },
            "src/engines/strategy/interfaces.py": {
                "typing",
                "src.engines.strategy.models",
            },
            "src/engines/strategy/models.py": {
                "dataclasses",
                "enum",
                "src.engines.research.orb.models",
            },
        }

        for path, expected in expected_imports.items():
            with self.subTest(path=path), open(path, encoding="utf-8") as source_file:
                tree = ast.parse(source_file.read())
            imported_modules = {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module is not None
            }
            self.assertEqual(imported_modules, expected)


class _NoActionStrategy:
    """Test-only deterministic implementation of the structural protocol."""

    def evaluate(self, context: StrategyContext) -> StrategyDecision:
        """Return the explicit non-executing placeholder decision."""
        return StrategyDecision(
            context=context,
            decision_type=StrategyDecisionType.NO_ACTION,
        )


def _evaluate_strategy(
    strategy: Strategy,
    context: StrategyContext,
) -> StrategyDecision:
    """Exercise the public protocol through a typed structural consumer."""
    return strategy.evaluate(context)


def _context() -> StrategyContext:
    """Create one existing-record context for structural contract tests."""
    record = _record(high=106.0)
    return build_strategy_context(record, build_behavior_atlas((record,)))


def _record(*, high: float):
    """Build one completed no-escape research record without market analysis."""
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
    """Return a canonical Asia/Kolkata timestamp for immutable test evidence."""
    return datetime(2026, 7, 17, hour, minute, tzinfo=ZoneInfo("Asia/Kolkata"))
