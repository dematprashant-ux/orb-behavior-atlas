"""Immutable domain concepts and observed-fact operations for ORB sessions."""

from src.engines.research.orb.classification import classify_orb_behavior
from src.engines.research.orb.comparison import compare_behavior_atlases
from src.engines.research.orb.descriptive import (
    compute_behavior_descriptive_statistics,
)
from src.engines.research.orb.distributions import compute_behavior_distributions
from src.engines.research.orb.atlas import build_behavior_atlas
from src.engines.research.orb.escape import find_first_escape_event
from src.engines.research.orb.extraction import extract_opening_range
from src.engines.research.orb.features import generate_orb_features
from src.engines.research.orb.findings import (
    create_research_finding,
    request_statistical_validation,
)
from src.engines.research.orb.hypothesis import evaluate_behavior_hypothesis
from src.engines.research.orb.grouping import (
    group_by_behavior,
    group_by_escape_direction,
    group_by_return_to_range,
)
from src.engines.research.orb.models import (
    OpeningRange,
    ORBBehavior,
    ORBBehaviorAtlas,
    ORBBehaviorAtlasGroups,
    ORBBehaviorComparison,
    ORBBehaviorDescriptiveStatistics,
    ORBBehaviorDistributions,
    ORBBehaviorHypothesis,
    ORBBehaviorHypothesisEvaluation,
    ORBResearchFinding,
    ORBResearchFindingStatus,
    ORBStatisticalComparisonDesign,
    ORBStatisticalEvidence,
    ORBStatisticalObservationDomain,
    ORBStatisticalTestFamily,
    ORBStatisticalTestDefinition,
    ORBStatisticalTestIdentifier,
    ORBStatisticalTestImplementationStatus,
    ORBStatisticalValidation,
    ORBStatisticalValidationLifecycleStatus,
    ORBStatisticalValidationNotEvaluableReason,
    ORBStatisticalValidationStatus,
    ORBBehaviorKind,
    ORBBehaviorRecord,
    ORBBehaviorStatistics,
    ORBEscapeDirection,
    ORBEscapeEvent,
    ORBFeatures,
    ORBFeatureSummary,
    ORBFeatureSummaryDifference,
    ORBHypothesisMetric,
    ORBHypothesisNotEvaluableReason,
    ORBHypothesisOutcome,
    ORBHypothesisRelation,
    ORBPostEscapeObservation,
    ORBSession,
    ORBWindow,
)
from src.engines.research.orb.observation import observe_post_escape
from src.engines.research.orb.record import build_behavior_record
from src.engines.research.orb.statistical_validation import (
    complete_statistical_validation,
    create_statistical_validation,
    mark_statistical_validation_not_evaluable,
)
from src.engines.research.orb.statistical_tests import (
    get_statistical_test_definition,
    list_statistical_test_definitions,
    list_statistical_test_definitions_by_family,
)
from src.engines.research.orb.statistics import compute_behavior_statistics

__all__ = [
    "OpeningRange",
    "ORBBehavior",
    "ORBBehaviorAtlas",
    "ORBBehaviorAtlasGroups",
    "ORBBehaviorComparison",
    "ORBBehaviorDescriptiveStatistics",
    "ORBBehaviorDistributions",
    "ORBBehaviorHypothesis",
    "ORBBehaviorHypothesisEvaluation",
    "ORBResearchFinding",
    "ORBResearchFindingStatus",
    "ORBStatisticalComparisonDesign",
    "ORBStatisticalEvidence",
    "ORBStatisticalObservationDomain",
    "ORBStatisticalTestFamily",
    "ORBStatisticalTestDefinition",
    "ORBStatisticalTestIdentifier",
    "ORBStatisticalTestImplementationStatus",
    "ORBStatisticalValidation",
    "ORBStatisticalValidationLifecycleStatus",
    "ORBStatisticalValidationNotEvaluableReason",
    "ORBStatisticalValidationStatus",
    "ORBBehaviorKind",
    "ORBBehaviorRecord",
    "ORBBehaviorStatistics",
    "ORBEscapeDirection",
    "ORBEscapeEvent",
    "ORBFeatures",
    "ORBFeatureSummary",
    "ORBFeatureSummaryDifference",
    "ORBHypothesisMetric",
    "ORBHypothesisNotEvaluableReason",
    "ORBHypothesisOutcome",
    "ORBHypothesisRelation",
    "ORBPostEscapeObservation",
    "ORBSession",
    "ORBWindow",
    "build_behavior_record",
    "build_behavior_atlas",
    "classify_orb_behavior",
    "complete_statistical_validation",
    "compare_behavior_atlases",
    "compute_behavior_descriptive_statistics",
    "compute_behavior_distributions",
    "compute_behavior_statistics",
    "extract_opening_range",
    "create_research_finding",
    "create_statistical_validation",
    "evaluate_behavior_hypothesis",
    "find_first_escape_event",
    "generate_orb_features",
    "get_statistical_test_definition",
    "group_by_behavior",
    "group_by_escape_direction",
    "group_by_return_to_range",
    "observe_post_escape",
    "mark_statistical_validation_not_evaluable",
    "list_statistical_test_definitions",
    "list_statistical_test_definitions_by_family",
    "request_statistical_validation",
]
