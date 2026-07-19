"""Deterministic delegation through existing strategy and execution contracts."""

from src.engines.backtesting.builders import build_backtest_run
from src.engines.backtesting.models import BacktestContext, BacktestRun, BacktestStatus
from src.engines.execution.builders import build_execution_request
from src.engines.execution.models import ExecutionResult
from src.engines.strategy.context import build_strategy_context
from src.engines.strategy.models import StrategyDecision

__all__ = ["DeterministicBacktestEngine"]


class DeterministicBacktestEngine:
    """Orchestrate existing historical records through injected service contracts.

    The engine preserves atlas order and delegates all strategy and execution
    behavior. It neither replays market data nor performs simulation,
    calculations, reporting, persistence, or I/O.
    """

    def run(self, context: BacktestContext) -> BacktestRun:
        """Evaluate and execute every existing behavior record in atlas order.

        Args:
            context: Existing immutable research artifacts and injected services.

        Returns:
            A completed immutable run retaining delegated execution results.

        Raises:
            TypeError: If the context or a delegated protocol result is invalid.
        """
        if not isinstance(context, BacktestContext):
            raise TypeError("context must be a BacktestContext.")

        execution_results: list[ExecutionResult] = []
        for record in context.behavior_atlas:
            strategy_context = build_strategy_context(record, context.behavior_atlas)
            decision = context.strategy.evaluate(strategy_context)
            if not isinstance(decision, StrategyDecision):
                raise TypeError("strategy.evaluate must return a StrategyDecision.")

            request = build_execution_request(decision)
            execution_result = context.execution_engine.execute(request)
            if not isinstance(execution_result, ExecutionResult):
                raise TypeError(
                    "execution_engine.execute must return an ExecutionResult."
                )
            execution_results.append(execution_result)

        return build_backtest_run(
            context,
            BacktestStatus.COMPLETED,
            execution_results,
        )
