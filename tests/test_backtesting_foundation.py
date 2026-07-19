"""Contract tests for immutable Backtesting Engine foundation boundaries."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestEngine,
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
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import ORBRuleStrategy


class BacktestingFoundationTests(TestCase):
    """Verify the backtesting boundary is immutable, typed, and behavior-free."""

    def test_builders_retain_existing_context_dependencies_by_reference(self) -> None:
        """Compose historical artifacts and injected services without copying state."""
        atlas = ORBBehaviorAtlas(records=())
        strategy = ORBRuleStrategy()
        execution_engine = _SkippedExecutionEngine()

        context = build_backtest_context(atlas, strategy, execution_engine)
        run = build_backtest_run(context, BacktestStatus.CREATED)

        self.assertIsInstance(context, BacktestContext)
        self.assertIsInstance(run, BacktestRun)
        self.assertIs(context.behavior_atlas, atlas)
        self.assertIs(context.strategy, strategy)
        self.assertIs(context.execution_engine, execution_engine)
        self.assertIs(run.context, context)
        self.assertIs(run.status, BacktestStatus.CREATED)

    def test_models_are_immutable_and_status_values_are_stable(self) -> None:
        """Expose frozen models and lifecycle labels without run behavior."""
        context = _context()
        run = build_backtest_run(context, BacktestStatus.RUNNING)

        self.assertTrue(is_dataclass(context))
        self.assertTrue(is_dataclass(run))
        self.assertFalse(hasattr(context, "__dict__"))
        self.assertFalse(hasattr(run, "__dict__"))
        self.assertEqual(BacktestStatus.CREATED.value, "CREATED")
        self.assertEqual(BacktestStatus.RUNNING.value, "RUNNING")
        self.assertEqual(BacktestStatus.COMPLETED.value, "COMPLETED")
        self.assertEqual(BacktestStatus.FAILED.value, "FAILED")
        with self.assertRaises(FrozenInstanceError):
            context.strategy = ORBRuleStrategy()
        with self.assertRaises(FrozenInstanceError):
            run.status = BacktestStatus.FAILED

    def test_builders_are_deterministic(self) -> None:
        """Return equal structural values for the same immutable input objects."""
        atlas = ORBBehaviorAtlas(records=())
        strategy = ORBRuleStrategy()
        execution_engine = _SkippedExecutionEngine()
        context = build_backtest_context(atlas, strategy, execution_engine)

        self.assertEqual(
            context,
            build_backtest_context(atlas, strategy, execution_engine),
        )
        self.assertEqual(
            build_backtest_run(context, BacktestStatus.COMPLETED),
            build_backtest_run(context, BacktestStatus.COMPLETED),
        )

    def test_builders_reject_intrinsic_misuse(self) -> None:
        """Require an atlas and non-null injected services without invoking them."""
        context = _context()

        with self.assertRaises(TypeError):
            build_backtest_context(
                object(),
                ORBRuleStrategy(),
                _SkippedExecutionEngine(),
            )
        with self.assertRaises(TypeError):
            build_backtest_context(
                ORBBehaviorAtlas(records=()),
                None,
                _SkippedExecutionEngine(),
            )
        with self.assertRaises(TypeError):
            build_backtest_context(
                ORBBehaviorAtlas(records=()),
                ORBRuleStrategy(),
                None,
            )
        with self.assertRaises(TypeError):
            build_backtest_run(object(), BacktestStatus.CREATED)
        with self.assertRaises(TypeError):
            build_backtest_run(context, "CREATED")
        with self.assertRaises(TypeError):
            BacktestRun(context=context, status="CREATED")

    def test_backtest_protocol_supports_a_pure_structural_implementation(self) -> None:
        """Confirm the protocol accepts a deterministic non-simulating test engine."""
        context = _context()
        run = _run(_CreatedBacktestEngine(), context)

        self.assertIs(run.context, context)
        self.assertIs(run.status, BacktestStatus.CREATED)

    def test_backtesting_modules_depend_only_on_existing_engine_contracts(self) -> None:
        """Keep the foundation independent from data, fills, and performance logic."""
        expected_imports = {
            "src/engines/backtesting/builders.py": {
                "src.engines.backtesting.models",
                "src.engines.execution.interfaces",
                "src.engines.research.orb.models",
                "src.engines.strategy.interfaces",
            },
            "src/engines/backtesting/interfaces.py": {
                "typing",
                "src.engines.backtesting.models",
            },
            "src/engines/backtesting/models.py": {
                "dataclasses",
                "enum",
                "src.engines.execution.interfaces",
                "src.engines.research.orb.models",
                "src.engines.strategy.interfaces",
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


class _CreatedBacktestEngine:
    """Test-only deterministic implementation of the backtest protocol."""

    def run(self, context: BacktestContext) -> BacktestRun:
        """Return a structural created run without historical replay."""
        return build_backtest_run(context, BacktestStatus.CREATED)


def _run(engine: BacktestEngine, context: BacktestContext) -> BacktestRun:
    """Exercise the public protocol through a typed structural consumer."""
    return engine.run(context)


def _context() -> BacktestContext:
    """Build one immutable context with empty historical artifacts for tests."""
    return build_backtest_context(
        ORBBehaviorAtlas(records=()),
        ORBRuleStrategy(),
        _SkippedExecutionEngine(),
    )
