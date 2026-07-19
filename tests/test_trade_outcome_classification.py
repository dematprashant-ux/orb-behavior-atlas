"""Contract tests for immutable non-financial trade outcome classification."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime
from unittest import TestCase
from zoneinfo import ZoneInfo

from src.engines.backtesting import (
    BacktestRun,
    BacktestStatus,
    build_backtest_context,
    build_backtest_run,
)
from src.engines.data.models import Candle, Instrument, Timeframe
from src.engines.execution import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    build_execution_request,
    build_execution_result,
)
from src.engines.performance import (
    TradeOutcome,
    TradeOutcomeEngine,
    TradeOutcomeType,
    build_trade_outcome,
)
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
    ORBRuleStrategy,
    StrategyContext,
    StrategyDecision,
    StrategyDecisionType,
)


class TradeOutcomeClassificationTests(TestCase):
    """Verify immutable status mapping over existing execution-result facts."""

    def test_builder_maps_every_existing_execution_status(self) -> None:
        """Map statuses without adding financial or duplicated execution facts."""
        cases = (
            (ExecutionStatus.ACCEPTED, TradeOutcomeType.EXECUTED),
            (ExecutionStatus.REJECTED, TradeOutcomeType.REJECTED),
            (ExecutionStatus.SKIPPED, TradeOutcomeType.SKIPPED),
        )

        for execution_status, outcome_type in cases:
            with self.subTest(execution_status=execution_status):
                execution_result = _execution_result(execution_status)

                outcome = build_trade_outcome(execution_result)

                self.assertIsInstance(outcome, TradeOutcome)
                self.assertIs(outcome.execution_result, execution_result)
                self.assertIs(outcome.outcome_type, outcome_type)

    def test_engine_classifies_each_result_in_existing_run_order(self) -> None:
        """Produce one immutable outcome per result without changing the run."""
        execution_results = (
            _execution_result(ExecutionStatus.SKIPPED),
            _execution_result(ExecutionStatus.ACCEPTED),
            _execution_result(ExecutionStatus.REJECTED),
        )
        backtest_run = _backtest_run(execution_results)

        outcomes = TradeOutcomeEngine().classify(backtest_run)

        self.assertIsInstance(outcomes, tuple)
        self.assertEqual(len(outcomes), len(execution_results))
        self.assertEqual(
            tuple(outcome.outcome_type for outcome in outcomes),
            (
                TradeOutcomeType.SKIPPED,
                TradeOutcomeType.EXECUTED,
                TradeOutcomeType.REJECTED,
            ),
        )
        for execution_result, outcome in zip(
            execution_results,
            outcomes,
            strict=True,
        ):
            self.assertIs(outcome.execution_result, execution_result)

    def test_classification_is_deterministic_and_outcomes_are_immutable(self) -> None:
        """Return equal outputs from immutable inputs without mutating child results."""
        backtest_run = _backtest_run((_execution_result(ExecutionStatus.ACCEPTED),))
        engine = TradeOutcomeEngine()

        first = engine.classify(backtest_run)
        second = engine.classify(backtest_run)

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first[0]))
        self.assertFalse(hasattr(first[0], "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first[0].outcome_type = TradeOutcomeType.SKIPPED

    def test_classifier_rejects_intrinsic_misuse(self) -> None:
        """Require the existing BacktestRun and ExecutionResult model types."""
        with self.assertRaises(TypeError):
            TradeOutcomeEngine().classify(object())
        with self.assertRaises(TypeError):
            build_trade_outcome(object())
        with self.assertRaises(TypeError):
            TradeOutcome(object(), TradeOutcomeType.EXECUTED)
        with self.assertRaises(TypeError):
            TradeOutcome(_execution_result(ExecutionStatus.ACCEPTED), "EXECUTED")
        with self.assertRaises(ValueError):
            TradeOutcome(
                _execution_result(ExecutionStatus.ACCEPTED),
                TradeOutcomeType.REJECTED,
            )

    def test_classifier_depends_only_on_existing_contract_boundaries(self) -> None:
        """Keep classification independent from markets and financial analytics."""
        with open(
            "src/engines/performance/outcomes.py",
            encoding="utf-8",
        ) as source_file:
            tree = ast.parse(source_file.read())

        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(
            imported_modules,
            {
                "src.engines.backtesting.models",
                "src.engines.execution.models",
                "src.engines.performance.models",
            },
        )


class _UnusedExecutionEngine:
    """Test-only backtest dependency unused by outcome-only fixtures."""

    def execute(self, request: ExecutionRequest) -> object:
        """Return no execution result because fixture construction bypasses execution."""
        return object()


def _backtest_run(execution_results: tuple[ExecutionResult, ...]) -> BacktestRun:
    """Build an immutable run from existing fixture execution results only."""
    decision = _decision()
    context = build_backtest_context(
        decision.context.atlas,
        ORBRuleStrategy(),
        _UnusedExecutionEngine(),
    )
    return build_backtest_run(
        context,
        BacktestStatus.COMPLETED,
        execution_results,
    )


def _execution_result(execution_status: ExecutionStatus) -> ExecutionResult:
    """Build one immutable execution result with an existing immutable decision."""
    return build_execution_result(
        build_execution_request(_decision()),
        execution_status,
    )


def _decision() -> StrategyDecision:
    """Build a no-action decision from minimal valid immutable research outputs."""
    candle = Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=datetime(2026, 7, 17, 9, 15, tzinfo=ZoneInfo("Asia/Kolkata")),
        session_date=date(2026, 7, 17),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=1,
    )
    opening_range = OpeningRange(
        window=ORBWindow(candle.timestamp, candle.timestamp),
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
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
        range_size=opening_range.high - opening_range.low,
    )
    record = build_behavior_record(opening_range, None, None, behavior, features)
    atlas = build_behavior_atlas((record,))
    return StrategyDecision(
        StrategyContext(record=record, atlas=atlas),
        StrategyDecisionType.NO_ACTION,
    )
