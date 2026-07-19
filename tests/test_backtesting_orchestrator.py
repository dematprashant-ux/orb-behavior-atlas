"""Contract tests for deterministic Backtesting Engine orchestration."""

import ast
from dataclasses import FrozenInstanceError
from datetime import date, datetime
from unittest import TestCase
from zoneinfo import ZoneInfo

from src.engines.backtesting import (
    BacktestEngine,
    BacktestStatus,
    DeterministicBacktestEngine,
    build_backtest_context,
)
from src.engines.data.models import Candle, Instrument, Timeframe
from src.engines.execution import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    build_execution_result,
)
from src.engines.research import (
    OpeningRange,
    ORBBehavior,
    ORBBehaviorAtlas,
    ORBBehaviorKind,
    ORBBehaviorRecord,
    ORBFeatures,
    ORBWindow,
    build_behavior_atlas,
    build_behavior_record,
)
from src.engines.strategy import (
    StrategyContext,
    StrategyDecision,
    StrategyDecisionType,
)


class DeterministicBacktestEngineTests(TestCase):
    """Verify orchestration delegates without replay or execution simulation."""

    def test_run_delegates_each_record_in_atlas_order(self) -> None:
        """Build contexts and requests before delegating existing service behavior."""
        records = (_record(100.0), _record(110.0))
        atlas = build_behavior_atlas(records)
        strategy = _RecordingStrategy()
        execution_engine = _RecordingExecutionEngine()
        context = build_backtest_context(atlas, strategy, execution_engine)

        run = DeterministicBacktestEngine().run(context)

        self.assertIs(run.context, context)
        self.assertIs(run.status, BacktestStatus.COMPLETED)
        self.assertEqual(
            tuple(strategy_context.record for strategy_context in strategy.contexts),
            records,
        )
        self.assertEqual(len(execution_engine.requests), len(records))
        self.assertEqual(len(run.execution_results), len(records))
        for index, (record, result) in enumerate(
            zip(records, run.execution_results, strict=True)
        ):
            self.assertIs(result.request.decision.context.record, record)
            self.assertIs(result.request.decision.context.atlas, atlas)
            self.assertIs(result.request, execution_engine.requests[index])

    def test_run_is_deterministic_and_returns_immutable_results(self) -> None:
        """Repeated delegation with unchanged inputs returns equal frozen results."""
        context = build_backtest_context(
            build_behavior_atlas((_record(100.0),)),
            _RecordingStrategy(),
            _RecordingExecutionEngine(),
        )
        engine: BacktestEngine = DeterministicBacktestEngine()

        first = engine.run(context)
        second = engine.run(context)

        self.assertEqual(first, second)
        self.assertIsInstance(first.execution_results, tuple)
        with self.assertRaises(FrozenInstanceError):
            first.execution_results = ()

    def test_run_supports_an_empty_atlas_without_service_calls(self) -> None:
        """Return a completed empty result set without fabricating execution work."""
        strategy = _RecordingStrategy()
        execution_engine = _RecordingExecutionEngine()
        context = build_backtest_context(
            ORBBehaviorAtlas(records=()),
            strategy,
            execution_engine,
        )

        run = DeterministicBacktestEngine().run(context)

        self.assertIs(run.status, BacktestStatus.COMPLETED)
        self.assertEqual(run.execution_results, ())
        self.assertEqual(strategy.contexts, [])
        self.assertEqual(execution_engine.requests, [])

    def test_run_rejects_invalid_intrinsic_and_protocol_outputs(self) -> None:
        """Require a context and existing contract result models from services."""
        engine = DeterministicBacktestEngine()
        atlas = build_behavior_atlas((_record(100.0),))

        with self.assertRaises(TypeError):
            engine.run(object())
        with self.assertRaisesRegex(TypeError, "StrategyDecision"):
            engine.run(
                build_backtest_context(
                    atlas,
                    _InvalidStrategy(),
                    _RecordingExecutionEngine(),
                )
            )
        with self.assertRaisesRegex(TypeError, "ExecutionResult"):
            engine.run(
                build_backtest_context(
                    atlas,
                    _RecordingStrategy(),
                    _InvalidExecutionEngine(),
                )
            )

    def test_orchestrator_imports_only_existing_contract_boundaries(self) -> None:
        """Keep orchestration independent from data replay and performance logic."""
        with open(
            "src/engines/backtesting/orchestrator.py",
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
                "src.engines.backtesting.builders",
                "src.engines.backtesting.models",
                "src.engines.execution.builders",
                "src.engines.execution.models",
                "src.engines.strategy.context",
                "src.engines.strategy.models",
            },
        )


class _RecordingStrategy:
    """Test-only strategy that records contexts and returns an existing decision."""

    def __init__(self) -> None:
        """Initialize ordered test evidence for delegated strategy contexts."""
        self.contexts: list[StrategyContext] = []

    def evaluate(self, context: StrategyContext) -> StrategyDecision:
        """Retain context evidence and return a no-action structural decision."""
        self.contexts.append(context)
        return StrategyDecision(context, StrategyDecisionType.NO_ACTION)


class _RecordingExecutionEngine:
    """Test-only execution service that records requests without fill simulation."""

    def __init__(self) -> None:
        """Initialize ordered test evidence for delegated execution requests."""
        self.requests: list[ExecutionRequest] = []

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Retain request evidence and return a structural skipped result."""
        self.requests.append(request)
        return build_execution_result(request, ExecutionStatus.SKIPPED)


class _InvalidStrategy:
    """Test-only strategy that violates the public strategy result contract."""

    def evaluate(self, context: StrategyContext) -> object:
        """Return an unsupported object to exercise protocol-boundary rejection."""
        return object()


class _InvalidExecutionEngine:
    """Test-only execution service that violates the execution result contract."""

    def execute(self, request: ExecutionRequest) -> object:
        """Return an unsupported object to exercise protocol-boundary rejection."""
        return object()


def _record(open_price: float) -> ORBBehaviorRecord:
    """Build one no-escape record with unique existing observed opening facts."""
    candle = Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=datetime(2026, 7, 17, 9, 15, tzinfo=ZoneInfo("Asia/Kolkata")),
        session_date=date(2026, 7, 17),
        open=open_price,
        high=open_price + 2.0,
        low=open_price - 1.0,
        close=open_price + 1.0,
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
    return build_behavior_record(opening_range, None, None, behavior, features)
