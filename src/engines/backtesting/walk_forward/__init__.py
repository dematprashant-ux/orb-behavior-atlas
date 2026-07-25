"""Walk-forward domain models and deterministic dataset-window boundaries."""

from src.engines.backtesting.walk_forward.models import (
    DateTimeRange,
    WalkForwardPlan,
    WalkForwardWindow,
)
from src.engines.backtesting.walk_forward.dataset import (
    DatasetWindow,
    DatasetWindowBuilder,
    StandardDatasetWindowBuilder,
)
from src.engines.backtesting.walk_forward.split import (
    StandardTrainingValidationSplitEngine,
    TrainingValidationSplitEngine,
    WalkForwardDatasetSplit,
)
from src.engines.backtesting.walk_forward.rolling import (
    RollingWindowGenerator,
    StandardRollingWindowGenerator,
    WalkForwardConfiguration,
)
from src.engines.backtesting.walk_forward.execution import (
    WalkForwardSelection,
    WalkForwardTrainer,
    WalkForwardValidationExecutor,
    WalkForwardValidationResult,
)
from src.engines.backtesting.walk_forward.runner import (
    StandardWalkForwardRunner,
    WalkForwardIterationResult,
    WalkForwardRun,
    WalkForwardRunner,
)
from src.engines.backtesting.walk_forward.reporting import (
    StandardWalkForwardAnalyticsPipeline,
    StandardWalkForwardReportBuilder,
    WalkForwardAnalyticsPipeline,
    WalkForwardReport,
    WalkForwardReportBuilder,
    WalkForwardReportType,
    WalkForwardStructuralSummary,
)
from src.engines.backtesting.walk_forward.serialization import (
    DictionaryWalkForwardReportSerializer,
)
from src.engines.backtesting.walk_forward.rendering import (
    StandardWalkForwardHtmlRenderer,
    StandardWalkForwardMarkdownRenderer,
)
from src.engines.backtesting.walk_forward.pdf import StandardWalkForwardPdfRenderer

__all__ = [
    "DatasetWindow",
    "DatasetWindowBuilder",
    "DateTimeRange",
    "StandardDatasetWindowBuilder",
    "StandardTrainingValidationSplitEngine",
    "StandardRollingWindowGenerator",
    "StandardWalkForwardRunner",
    "StandardWalkForwardAnalyticsPipeline",
    "StandardWalkForwardHtmlRenderer",
    "StandardWalkForwardMarkdownRenderer",
    "StandardWalkForwardPdfRenderer",
    "StandardWalkForwardReportBuilder",
    "TrainingValidationSplitEngine",
    "RollingWindowGenerator",
    "WalkForwardConfiguration",
    "WalkForwardDatasetSplit",
    "WalkForwardIterationResult",
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
]
