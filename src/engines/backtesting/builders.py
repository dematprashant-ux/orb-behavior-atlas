"""Pure construction of immutable Backtesting Engine contexts and runs."""

from collections.abc import Sequence

from src.engines.backtesting.models import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
)
from src.engines.execution.interfaces import ExecutionEngine
from src.engines.execution.models import ExecutionResult
from src.engines.research.orb.models import ORBBehaviorAtlas
from src.engines.strategy.interfaces import Strategy

__all__ = ["build_backtest_context", "build_backtest_run"]


def build_backtest_context(
    behavior_atlas: ORBBehaviorAtlas,
    strategy: Strategy,
    execution_engine: ExecutionEngine,
) -> BacktestContext:
    """Build a context retaining existing historical artifacts and services.

    The builder invokes neither injected service and performs no replay,
    simulation, execution, or performance calculation.

    Args:
        behavior_atlas: Existing immutable historical research artifacts.
        strategy: Injected strategy service for a future backtest implementation.
        execution_engine: Injected execution service for a future implementation.

    Returns:
        An immutable context retaining every supplied object by reference.

    Raises:
        TypeError: If the atlas is invalid or an injected service is ``None``.
    """
    if not isinstance(behavior_atlas, ORBBehaviorAtlas):
        raise TypeError("behavior_atlas must be an ORBBehaviorAtlas.")
    if strategy is None:
        raise TypeError("strategy must not be None.")
    if execution_engine is None:
        raise TypeError("execution_engine must not be None.")

    return BacktestContext(
        behavior_atlas=behavior_atlas,
        strategy=strategy,
        execution_engine=execution_engine,
    )


def build_backtest_run(
    context: BacktestContext,
    status: BacktestStatus,
    execution_results: Sequence[ExecutionResult] = (),
) -> BacktestRun:
    """Build a run that retains a context and immutable execution-result references.

    Args:
        context: Existing immutable backtest context.
        status: Structural lifecycle status for the run.
        execution_results: Existing delegated execution results in canonical order.

    Returns:
        An immutable run referencing ``context`` and result objects.

    Raises:
        TypeError: If an input has an unsupported model type.
    """
    if not isinstance(context, BacktestContext):
        raise TypeError("context must be a BacktestContext.")
    if not isinstance(status, BacktestStatus):
        raise TypeError("status must be a BacktestStatus.")
    if not isinstance(execution_results, Sequence):
        raise TypeError(
            "execution_results must be a sequence of ExecutionResult values."
        )
    if any(
        not isinstance(execution_result, ExecutionResult)
        for execution_result in execution_results
    ):
        raise TypeError("execution_results must contain only ExecutionResult values.")
    return BacktestRun(
        context=context,
        status=status,
        execution_results=tuple(execution_results),
    )
