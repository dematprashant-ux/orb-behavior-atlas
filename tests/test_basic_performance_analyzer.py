"""Contract tests for deterministic basic Performance Analytics."""

import ast
from dataclasses import FrozenInstanceError
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
    ExecutionStatus,
    build_execution_request,
    build_execution_result,
)
from src.engines.performance import (
    BasicPerformanceEngine,
    PerformanceEngine,
    PerformanceStatus,
    build_performance_context,
    build_performance_report,
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


class BasicPerformanceEngineTests(TestCase):
    """Verify deterministic counting over existing immutable execution outcomes."""

    def test_analyze_returns_only_existing_execution_status_counts(self) -> None:
        """Count statuses without evaluating strategy or inspecting market data."""
        context = build_performance_context(
            _completed_run(
                (
                    ExecutionStatus.ACCEPTED,
                    ExecutionStatus.REJECTED,
                    ExecutionStatus.REJECTED,
                    ExecutionStatus.SKIPPED,
                    ExecutionStatus.SKIPPED,
                    ExecutionStatus.SKIPPED,
                )
            )
        )

        report = BasicPerformanceEngine().analyze(context)

        self.assertIs(report.context, context)
        self.assertIs(report.status, PerformanceStatus.ANALYZED)
        self.assertEqual(report.total_execution_results, 6)
        self.assertEqual(report.accepted_count, 1)
        self.assertEqual(report.rejected_count, 2)
        self.assertEqual(report.skipped_count, 3)

    def test_analyze_is_deterministic_and_report_is_immutable(self) -> None:
        """Return equal immutable reports from unchanged immutable input objects."""
        context = build_performance_context(
            _completed_run((ExecutionStatus.ACCEPTED, ExecutionStatus.SKIPPED))
        )
        engine: PerformanceEngine = BasicPerformanceEngine()

        first = engine.analyze(context)
        second = engine.analyze(context)

        self.assertEqual(first, second)
        with self.assertRaises(FrozenInstanceError):
            first.accepted_count = 0

    def test_analyze_supports_a_completed_run_with_no_execution_results(self) -> None:
        """Report zero counts without fabricating execution or financial outcomes."""
        report = BasicPerformanceEngine().analyze(
            build_performance_context(_completed_run(()))
        )

        self.assertEqual(report.total_execution_results, 0)
        self.assertEqual(report.accepted_count, 0)
        self.assertEqual(report.rejected_count, 0)
        self.assertEqual(report.skipped_count, 0)

    def test_analyze_rejects_intrinsic_misuse(self) -> None:
        """Require a context referencing a completed backtest run."""
        engine = BasicPerformanceEngine()

        with self.assertRaises(TypeError):
            engine.analyze(object())
        with self.assertRaisesRegex(ValueError, "COMPLETED"):
            engine.analyze(
                build_performance_context(_backtest_run(BacktestStatus.CREATED, ()))
            )

        context = build_performance_context(_completed_run(()))
        with self.assertRaises(ValueError):
            build_performance_report(
                context,
                PerformanceStatus.ANALYZED,
                total_execution_results=1,
                accepted_count=1,
                rejected_count=1,
            )
        with self.assertRaises(TypeError):
            build_performance_report(
                context,
                PerformanceStatus.ANALYZED,
                total_execution_results=True,
            )

    def test_analyzer_depends_only_on_existing_contract_boundaries(self) -> None:
        """Keep analysis independent from candles, calculations, and I/O."""
        with open(
            "src/engines/performance/analyzer.py",
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
                "src.engines.performance.builders",
                "src.engines.performance.models",
            },
        )


class _SkippedExecutionEngine:
    """Test-only dependency retained by a structural backtest context."""

    def execute(self, request: ExecutionRequest) -> object:
        """Remain unused because test fixtures construct existing results directly."""
        return object()


def _completed_run(statuses: tuple[ExecutionStatus, ...]) -> BacktestRun:
    """Build a completed run containing immutable results with supplied statuses."""
    return _backtest_run(BacktestStatus.COMPLETED, statuses)


def _backtest_run(
    status: BacktestStatus,
    execution_statuses: tuple[ExecutionStatus, ...],
) -> BacktestRun:
    """Build a structural backtest run without replaying data or executing work."""
    decision = _decision()
    execution_results = tuple(
        build_execution_result(
            build_execution_request(decision),
            execution_status,
        )
        for execution_status in execution_statuses
    )
    backtest_context = build_backtest_context(
        decision.context.atlas,
        ORBRuleStrategy(),
        _SkippedExecutionEngine(),
    )
    return build_backtest_run(backtest_context, status, execution_results)


def _decision() -> StrategyDecision:
    """Build one existing no-action decision with real immutable research facts."""
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
