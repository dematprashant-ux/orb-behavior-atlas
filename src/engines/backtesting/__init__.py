"""Backtesting Engine structural contracts and pure construction functions."""

from src.engines.backtesting.builders import (
    build_backtest_context,
    build_backtest_run,
)
from src.engines.backtesting.costs import (
    FixedRateTransactionCostModel,
    TransactionCostBreakdown,
    ZeroTransactionCostModel,
)
from src.engines.backtesting.interfaces import BacktestEngine, TransactionCostModel
from src.engines.backtesting.models import BacktestContext, BacktestRun, BacktestStatus
from src.engines.backtesting.orchestrator import DeterministicBacktestEngine
from src.engines.backtesting.walk_forward import (
    DatasetWindow,
    DatasetWindowBuilder,
    DateTimeRange,
    StandardDatasetWindowBuilder,
    StandardTrainingValidationSplitEngine,
    StandardRollingWindowGenerator,
    TrainingValidationSplitEngine,
    RollingWindowGenerator,
    WalkForwardConfiguration,
    WalkForwardDatasetSplit,
    WalkForwardPlan,
    WalkForwardWindow,
)

__all__ = [
    "BacktestContext",
    "BacktestEngine",
    "BacktestRun",
    "BacktestStatus",
    "DeterministicBacktestEngine",
    "DateTimeRange",
    "DatasetWindow",
    "DatasetWindowBuilder",
    "FixedRateTransactionCostModel",
    "TransactionCostBreakdown",
    "TransactionCostModel",
    "StandardDatasetWindowBuilder",
    "StandardTrainingValidationSplitEngine",
    "StandardRollingWindowGenerator",
    "TrainingValidationSplitEngine",
    "RollingWindowGenerator",
    "WalkForwardConfiguration",
    "WalkForwardDatasetSplit",
    "ZeroTransactionCostModel",
    "WalkForwardPlan",
    "WalkForwardWindow",
    "build_backtest_context",
    "build_backtest_run",
]
