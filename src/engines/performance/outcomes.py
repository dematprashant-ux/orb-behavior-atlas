"""Pure immutable classification of existing execution outcomes."""

from src.engines.backtesting.models import BacktestRun
from src.engines.execution.models import ExecutionResult
from src.engines.performance.models import (
    TradeOutcome,
    TradeOutcomeType,
    _outcome_type_for,
)

__all__ = ["TradeOutcomeEngine", "build_trade_outcome"]


def build_trade_outcome(execution_result: ExecutionResult) -> TradeOutcome:
    """Classify one existing execution result without financial interpretation.

    Args:
        execution_result: Existing immutable execution result to classify.

    Returns:
        An immutable outcome retaining ``execution_result`` by reference.

    Raises:
        TypeError: If ``execution_result`` is not an ``ExecutionResult``.
    """
    if not isinstance(execution_result, ExecutionResult):
        raise TypeError("execution_result must be an ExecutionResult.")

    outcome_type = _outcome_type_for(execution_result.status)
    return TradeOutcome(
        execution_result=execution_result,
        outcome_type=outcome_type,
    )


class TradeOutcomeEngine:
    """Classify every existing execution result in a backtest run in order.

    The engine performs only status-to-outcome mapping. It does not inspect
    candles, perform executions, calculate financial metrics, mutate inputs, or
    perform I/O.
    """

    def classify(self, backtest_run: BacktestRun) -> tuple[TradeOutcome, ...]:
        """Return one immutable outcome for each existing execution result.

        Args:
            backtest_run: Existing immutable run whose results are classified.

        Returns:
            Immutable outcomes in the run's existing execution-result order.

        Raises:
            TypeError: If ``backtest_run`` is not a ``BacktestRun``.
        """
        if not isinstance(backtest_run, BacktestRun):
            raise TypeError("backtest_run must be a BacktestRun.")
        return tuple(
            build_trade_outcome(execution_result)
            for execution_result in backtest_run.execution_results
        )

