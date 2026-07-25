"""Execution Domain structural contracts and pure construction functions."""

from src.engines.execution.builders import (
    build_completed_trade,
    build_execution_request,
    build_execution_result,
)
from src.engines.execution.interfaces import ExecutionEngine
from src.engines.execution.models import (
    CompletedTrade,
    ExecutionRequest,
    ExecutionResult,
    ExecutionSide,
    ExecutionStatus,
)

__all__ = [
    "CompletedTrade",
    "ExecutionEngine",
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutionSide",
    "ExecutionStatus",
    "build_completed_trade",
    "build_execution_request",
    "build_execution_result",
]
