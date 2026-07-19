"""Contract tests for immutable Execution Domain foundation boundaries."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime
from unittest import TestCase
from zoneinfo import ZoneInfo

from src.engines.data.models import Candle, Instrument, Timeframe
from src.engines.execution import (
    ExecutionEngine,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    build_execution_request,
    build_execution_result,
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
    StrategyContext,
    StrategyDecision,
    StrategyDecisionType,
    build_strategy_context,
)


class ExecutionFoundationTests(TestCase):
    """Verify the execution boundary is immutable, typed, and behavior-free."""

    def test_builders_retain_existing_decision_and_request_references(self) -> None:
        """Aggregate immutable children without duplicating their stored values."""
        decision = _decision()

        request = build_execution_request(decision)
        result = build_execution_result(request, ExecutionStatus.SKIPPED)

        self.assertIsInstance(request, ExecutionRequest)
        self.assertIsInstance(result, ExecutionResult)
        self.assertIs(request.decision, decision)
        self.assertIs(result.request, request)
        self.assertIs(result.request.decision, decision)
        self.assertIs(result.status, ExecutionStatus.SKIPPED)

    def test_models_are_immutable_and_status_values_are_stable(self) -> None:
        """Expose frozen models and structural status labels only."""
        request = build_execution_request(_decision())
        result = build_execution_result(request, ExecutionStatus.ACCEPTED)

        self.assertTrue(is_dataclass(request))
        self.assertTrue(is_dataclass(result))
        self.assertFalse(hasattr(request, "__dict__"))
        self.assertFalse(hasattr(result, "__dict__"))
        self.assertEqual(ExecutionStatus.ACCEPTED.value, "ACCEPTED")
        self.assertEqual(ExecutionStatus.REJECTED.value, "REJECTED")
        self.assertEqual(ExecutionStatus.SKIPPED.value, "SKIPPED")
        with self.assertRaises(FrozenInstanceError):
            request.decision = _decision()
        with self.assertRaises(FrozenInstanceError):
            result.status = ExecutionStatus.REJECTED

    def test_builders_are_deterministic(self) -> None:
        """Return equal structural values for the same immutable input objects."""
        decision = _decision()
        request = build_execution_request(decision)

        self.assertEqual(request, build_execution_request(decision))
        self.assertEqual(
            build_execution_result(request, ExecutionStatus.REJECTED),
            build_execution_result(request, ExecutionStatus.REJECTED),
        )

    def test_builders_reject_intrinsic_misuse(self) -> None:
        """Require only the documented immutable child model types."""
        request = build_execution_request(_decision())

        with self.assertRaises(TypeError):
            build_execution_request(object())
        with self.assertRaises(TypeError):
            build_execution_result(object(), ExecutionStatus.ACCEPTED)
        with self.assertRaises(TypeError):
            build_execution_result(request, "ACCEPTED")
        with self.assertRaises(TypeError):
            ExecutionRequest(decision=object())
        with self.assertRaises(TypeError):
            ExecutionResult(request=request, status="ACCEPTED")

    def test_execution_protocol_supports_a_pure_structural_implementation(self) -> None:
        """Confirm the contract accepts a deterministic non-executing test engine."""
        request = build_execution_request(_decision())
        result = _execute(_SkippedExecutionEngine(), request)

        self.assertIs(result.request, request)
        self.assertIs(result.status, ExecutionStatus.SKIPPED)

    def test_execution_modules_depend_only_on_strategy_models_and_protocols(
        self,
    ) -> None:
        """Keep the foundation independent from broker, market, and positions."""
        expected_imports = {
            "src/engines/execution/builders.py": {
                "src.engines.execution.models",
                "src.engines.strategy.models",
            },
            "src/engines/execution/interfaces.py": {
                "typing",
                "src.engines.execution.models",
            },
            "src/engines/execution/models.py": {
                "dataclasses",
                "enum",
                "src.engines.strategy.models",
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
    """Test-only deterministic implementation of the execution protocol."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a structural skipped result without simulating execution."""
        return build_execution_result(request, ExecutionStatus.SKIPPED)


def _execute(
    engine: ExecutionEngine,
    request: ExecutionRequest,
) -> ExecutionResult:
    """Exercise the public protocol through a typed structural consumer."""
    return engine.execute(request)


def _decision() -> StrategyDecision:
    """Build one existing structural no-action decision for execution tests."""
    record = _record()
    context = build_strategy_context(record, build_behavior_atlas((record,)))
    return StrategyDecision(
        context=context,
        decision_type=StrategyDecisionType.NO_ACTION,
    )


def _record():
    """Build one completed immutable no-escape record for context construction."""
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
    opening_range = OpeningRange(
        window=ORBWindow(candle.timestamp, _timestamp(9, 30)),
        open=100.0,
        high=106.0,
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
        range_size=8.0,
    )
    return build_behavior_record(opening_range, None, None, behavior, features)


def _timestamp(hour: int, minute: int) -> datetime:
    """Return a canonical Asia/Kolkata timestamp for immutable test evidence."""
    return datetime(2026, 7, 17, hour, minute, tzinfo=ZoneInfo("Asia/Kolkata"))
