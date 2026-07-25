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
from src.engines.backtesting.configuration import OptimizationConfiguration
from src.engines.backtesting.evaluation import CandidateEvaluation
from src.engines.backtesting.grid_search import (
    GridSearchRun,
    GridSearchRunner,
    StandardGridSearchRunner,
)
from src.engines.backtesting.interfaces import (
    BacktestEngine,
    CandidateEvaluator,
    TransactionCostModel,
)
from src.engines.backtesting.models import BacktestContext, BacktestRun, BacktestStatus
from src.engines.backtesting.objectives import (
    CandidateObjective,
    ObjectiveDirection,
    ObjectiveScore,
)
from src.engines.backtesting.orchestrator import DeterministicBacktestEngine
from src.engines.backtesting.optimization import (
    OptimizationRun,
    OptimizationRunner,
    StandardOptimizationRunner,
)
from src.engines.backtesting.ranking import (
    ObjectiveRanker,
    ObjectiveRanking,
    RankedObjectiveScore,
    StandardObjectiveRanker,
)
from src.engines.backtesting.specification import OptimizationSpecification
from src.engines.backtesting.search import OptimizationSearchRun
from src.engines.backtesting.strategies import (
    GridOptimizationStrategy,
    OptimizationStrategy,
)
from src.engines.backtesting.selection import (
    BestRankSelectionPolicy,
    ObjectiveSelection,
    SelectionPolicy,
    TopRankedSelectionPolicy,
)
from src.engines.backtesting.walk_forward import (
    DatasetWindow,
    DatasetWindowBuilder,
    DateTimeRange,
    StandardDatasetWindowBuilder,
    StandardTrainingValidationSplitEngine,
    StandardRollingWindowGenerator,
    StandardWalkForwardRunner,
    StandardWalkForwardAnalyticsPipeline,
    StandardWalkForwardHtmlRenderer,
    StandardWalkForwardMarkdownRenderer,
    StandardWalkForwardPdfRenderer,
    StandardWalkForwardReportBuilder,
    TrainingValidationSplitEngine,
    RollingWindowGenerator,
    WalkForwardConfiguration,
    WalkForwardDatasetSplit,
    WalkForwardIterationResult,
    WalkForwardPlan,
    WalkForwardRun,
    WalkForwardRunner,
    WalkForwardAnalyticsPipeline,
    WalkForwardReport,
    WalkForwardReportBuilder,
    WalkForwardReportType,
    WalkForwardStructuralSummary,
    DictionaryWalkForwardReportSerializer,
    WalkForwardSelection,
    WalkForwardTrainer,
    WalkForwardValidationExecutor,
    WalkForwardValidationResult,
    WalkForwardWindow,
)

__all__ = [
    "BacktestContext",
    "BacktestEngine",
    "BacktestRun",
    "BacktestStatus",
    "BestRankSelectionPolicy",
    "CandidateEvaluation",
    "CandidateEvaluator",
    "CandidateObjective",
    "DeterministicBacktestEngine",
    "DateTimeRange",
    "DatasetWindow",
    "DatasetWindowBuilder",
    "FixedRateTransactionCostModel",
    "GridSearchRun",
    "GridSearchRunner",
    "GridOptimizationStrategy",
    "ObjectiveDirection",
    "ObjectiveRanker",
    "ObjectiveRanking",
    "ObjectiveScore",
    "ObjectiveSelection",
    "OptimizationConfiguration",
    "OptimizationRun",
    "OptimizationRunner",
    "OptimizationSearchRun",
    "OptimizationSpecification",
    "OptimizationStrategy",
    "RankedObjectiveScore",
    "TransactionCostBreakdown",
    "TransactionCostModel",
    "StandardDatasetWindowBuilder",
    "StandardGridSearchRunner",
    "StandardObjectiveRanker",
    "StandardOptimizationRunner",
    "StandardTrainingValidationSplitEngine",
    "StandardRollingWindowGenerator",
    "StandardWalkForwardRunner",
    "SelectionPolicy",
    "StandardWalkForwardAnalyticsPipeline",
    "StandardWalkForwardHtmlRenderer",
    "StandardWalkForwardMarkdownRenderer",
    "StandardWalkForwardPdfRenderer",
    "StandardWalkForwardReportBuilder",
    "TrainingValidationSplitEngine",
    "TopRankedSelectionPolicy",
    "RollingWindowGenerator",
    "WalkForwardConfiguration",
    "WalkForwardDatasetSplit",
    "WalkForwardIterationResult",
    "ZeroTransactionCostModel",
    "WalkForwardPlan",
    "WalkForwardRun",
    "WalkForwardRunner",
    "WalkForwardAnalyticsPipeline",
    "WalkForwardReport",
    "WalkForwardReportBuilder",
    "WalkForwardReportType",
    "WalkForwardStructuralSummary",
    "DictionaryWalkForwardReportSerializer",
    "WalkForwardSelection",
    "WalkForwardTrainer",
    "WalkForwardValidationExecutor",
    "WalkForwardValidationResult",
    "WalkForwardWindow",
    "build_backtest_context",
    "build_backtest_run",
]
