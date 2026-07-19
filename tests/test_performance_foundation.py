"""Contract tests for immutable Performance Analytics foundation boundaries."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    build_backtest_context,
    build_backtest_run,
)
from src.engines.execution import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    build_execution_result,
)
from src.engines.performance import (
    PerformanceContext,
    PerformanceEngine,
    PerformanceReport,
    PerformanceStatus,
    build_performance_context,
    build_performance_report,
)
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import ORBRuleStrategy


class PerformanceFoundationTests(TestCase):
    """Verify the analytics boundary is immutable, typed, and behavior-free."""

    def test_builders_retain_existing_backtest_references(self) -> None:
        """Compose structural analytics objects without copying child state."""
        backtest_run = _backtest_run()

        context = build_performance_context(backtest_run)
        report = build_performance_report(context, PerformanceStatus.CREATED)

        self.assertIsInstance(context, PerformanceContext)
        self.assertIsInstance(report, PerformanceReport)
        self.assertIs(context.backtest_run, backtest_run)
        self.assertIs(report.context, context)
        self.assertIs(report.status, PerformanceStatus.CREATED)

    def test_models_are_immutable_and_status_values_are_stable(self) -> None:
        """Expose frozen models and lifecycle labels without metric behavior."""
        context = build_performance_context(_backtest_run())
        report = build_performance_report(context, PerformanceStatus.ANALYZED)

        self.assertTrue(is_dataclass(context))
        self.assertTrue(is_dataclass(report))
        self.assertFalse(hasattr(context, "__dict__"))
        self.assertFalse(hasattr(report, "__dict__"))
        self.assertEqual(PerformanceStatus.CREATED.value, "CREATED")
        self.assertEqual(PerformanceStatus.ANALYZED.value, "ANALYZED")
        self.assertEqual(PerformanceStatus.FAILED.value, "FAILED")
        with self.assertRaises(FrozenInstanceError):
            context.backtest_run = _backtest_run()
        with self.assertRaises(FrozenInstanceError):
            report.status = PerformanceStatus.FAILED

    def test_builders_are_deterministic(self) -> None:
        """Return equal structural values for the same immutable input objects."""
        backtest_run = _backtest_run()
        context = build_performance_context(backtest_run)

        self.assertEqual(context, build_performance_context(backtest_run))
        self.assertEqual(
            build_performance_report(context, PerformanceStatus.CREATED),
            build_performance_report(context, PerformanceStatus.CREATED),
        )

    def test_builders_reject_intrinsic_misuse(self) -> None:
        """Require only existing analytics and backtesting model types."""
        context = build_performance_context(_backtest_run())

        with self.assertRaises(TypeError):
            build_performance_context(object())
        with self.assertRaises(TypeError):
            build_performance_report(object(), PerformanceStatus.CREATED)
        with self.assertRaises(TypeError):
            build_performance_report(context, "CREATED")
        with self.assertRaises(TypeError):
            PerformanceContext(backtest_run=object())
        with self.assertRaises(TypeError):
            PerformanceReport(context=context, status="CREATED")

    def test_protocol_supports_a_pure_structural_implementation(self) -> None:
        """Confirm the protocol accepts a deterministic non-analytic test engine."""
        context = build_performance_context(_backtest_run())
        report = _analyze(_CreatedPerformanceEngine(), context)

        self.assertIs(report.context, context)
        self.assertIs(report.status, PerformanceStatus.CREATED)

    def test_modules_depend_only_on_backtesting_contracts(self) -> None:
        """Keep the foundation independent from metrics and infrastructure."""
        expected_imports = {
            "src/engines/performance/builders.py": {
                "src.engines.backtesting.models",
                "src.engines.performance.models",
            },
            "src/engines/performance/interfaces.py": {
                "typing",
                "src.engines.performance.models",
            },
            "src/engines/performance/models.py": {
                "dataclasses",
                "enum",
                "src.engines.backtesting.models",
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


class _SkippedExecutionEngine:
    """Test-only execution dependency that performs no execution behavior."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a structural skipped result for the supplied request."""
        return build_execution_result(request, ExecutionStatus.SKIPPED)


class _CreatedPerformanceEngine:
    """Test-only deterministic implementation of the performance protocol."""

    def analyze(self, context: PerformanceContext) -> PerformanceReport:
        """Return a structural created report without calculating any metrics."""
        return build_performance_report(context, PerformanceStatus.CREATED)


def _analyze(
    engine: PerformanceEngine,
    context: PerformanceContext,
) -> PerformanceReport:
    """Exercise the public protocol through a typed structural consumer."""
    return engine.analyze(context)


def _backtest_run() -> BacktestRun:
    """Build one existing immutable backtest run without historical replay."""
    context: BacktestContext = build_backtest_context(
        ORBBehaviorAtlas(records=()),
        ORBRuleStrategy(),
        _SkippedExecutionEngine(),
    )
    return build_backtest_run(context, BacktestStatus.CREATED)
