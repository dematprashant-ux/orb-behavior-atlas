"""Immutable observed-fact models for BANKNIFTY ORB research sessions."""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import TypeVar

from src.engines.data.models import Candle, Session

__all__ = [
    "OpeningRange",
    "ORBBehavior",
    "ORBBehaviorAtlas",
    "ORBBehaviorAtlasGroups",
    "ORBBehaviorDistributions",
    "ORBBehaviorDescriptiveStatistics",
    "ORBBehaviorComparison",
    "ORBBehaviorHypothesis",
    "ORBBehaviorHypothesisEvaluation",
    "ORBResearchFinding",
    "ORBResearchFindingStatus",
    "ORBStatisticalEvidence",
    "ORBStatisticalTestFamily",
    "ORBStatisticalTestIdentifier",
    "ORBStatisticalValidation",
    "ORBStatisticalValidationLifecycleStatus",
    "ORBStatisticalValidationNotEvaluableReason",
    "ORBStatisticalValidationStatus",
    "ORBHypothesisMetric",
    "ORBHypothesisNotEvaluableReason",
    "ORBHypothesisOutcome",
    "ORBHypothesisRelation",
    "ORBBehaviorRecord",
    "ORBBehaviorStatistics",
    "ORBBehaviorKind",
    "ORBEscapeDirection",
    "ORBEscapeEvent",
    "ORBFeatures",
    "ORBFeatureSummary",
    "ORBFeatureSummaryDifference",
    "ORBPostEscapeObservation",
    "ORBSession",
    "ORBWindow",
]

_DistributionCategory = TypeVar("_DistributionCategory")


@dataclass(frozen=True, slots=True)
class ORBWindow:
    """Identifies the canonical timestamp interval observed as an ORB window."""

    start_timestamp: datetime
    end_timestamp: datetime

    def __post_init__(self) -> None:
        """Require timezone-aware, non-descending window timestamps."""
        _require_timezone_aware(self.start_timestamp, "start_timestamp")
        _require_timezone_aware(self.end_timestamp, "end_timestamp")
        if self.end_timestamp < self.start_timestamp:
            raise ValueError("end_timestamp must not precede start_timestamp")


@dataclass(frozen=True, slots=True)
class OpeningRange:
    """Records observed canonical values and evidence for an opening range."""

    window: ORBWindow
    open: float
    high: float
    low: float
    close: float
    candles: tuple[Candle, ...]

    def __post_init__(self) -> None:
        """Require the observed high to be at least the observed low."""
        if self.high < self.low:
            raise ValueError("high must not be below low")


class ORBBehaviorKind(str, Enum):
    """Identifies the objective ORB behavior states supported by current facts."""

    NO_ESCAPE = "NO_ESCAPE"
    ESCAPE_WITH_RETURN = "ESCAPE_WITH_RETURN"
    ESCAPE_WITHOUT_RETURN = "ESCAPE_WITHOUT_RETURN"


@dataclass(frozen=True, slots=True)
class ORBBehavior:
    """Represents one immutable classification from existing ORB observations."""

    kind: ORBBehaviorKind


class ORBEscapeDirection(str, Enum):
    """Identifies the ORB boundary crossed by an observed escape candle."""

    UPWARD = "UPWARD"
    DOWNWARD = "DOWNWARD"


@dataclass(frozen=True, slots=True)
class ORBFeatures:
    """Standardized numerical and categorical projections of existing ORB facts."""

    behavior: ORBBehaviorKind
    escape_exists: bool
    escape_direction: ORBEscapeDirection | None
    returned_to_range: bool | None
    mfe: float | None
    mae: float | None
    range_size: float

    def __post_init__(self) -> None:
        """Keep feature presence and behavior-state facts internally consistent."""
        if self.range_size < 0:
            raise ValueError("range_size must be non-negative")
        if not self.escape_exists:
            if (
                self.behavior is not ORBBehaviorKind.NO_ESCAPE
                or self.escape_direction is not None
                or self.returned_to_range is not None
                or self.mfe is not None
                or self.mae is not None
            ):
                raise ValueError("no-escape features must contain only no-escape facts")
            return

        if self.escape_direction is None or self.returned_to_range is None:
            raise ValueError("escape features require direction and return facts")
        if (self.mfe is None) != (self.mae is None):
            raise ValueError("mfe and mae must be both known or both unknown")
        if self.mfe is not None and (self.mfe < 0 or self.mae < 0):
            raise ValueError("mfe and mae must be non-negative")
        expected_behavior = (
            ORBBehaviorKind.ESCAPE_WITH_RETURN
            if self.returned_to_range
            else ORBBehaviorKind.ESCAPE_WITHOUT_RETURN
        )
        if self.behavior is not expected_behavior:
            raise ValueError("behavior must match the supplied escape return fact")


@dataclass(frozen=True, slots=True)
class ORBEscapeEvent:
    """Records one observed canonical candle exiting an opening range boundary."""

    timestamp: datetime
    direction: ORBEscapeDirection
    candle: Candle
    boundary_crossed: float
    crossing_price: float

    def __post_init__(self) -> None:
        """Require a timestamp and crossing price consistent with the event facts."""
        _require_timezone_aware(self.timestamp, "timestamp")
        if self.timestamp != self.candle.timestamp:
            raise ValueError("timestamp must match the escape candle timestamp")
        if self.direction is ORBEscapeDirection.UPWARD:
            if self.crossing_price <= self.boundary_crossed:
                raise ValueError("upward crossing_price must exceed boundary_crossed")
        elif self.crossing_price >= self.boundary_crossed:
            raise ValueError("downward crossing_price must be below boundary_crossed")


@dataclass(frozen=True, slots=True)
class ORBPostEscapeObservation:
    """Records objective canonical price facts following an ORB escape event."""

    highest_price: float | None
    lowest_price: float | None
    maximum_favorable_excursion: float | None
    maximum_adverse_excursion: float | None
    returned_inside_range: bool
    first_return_inside_timestamp: datetime | None

    def __post_init__(self) -> None:
        """Keep return-state facts internally consistent and timezone-aware."""
        measurements = (
            self.highest_price,
            self.lowest_price,
            self.maximum_favorable_excursion,
            self.maximum_adverse_excursion,
        )
        if any(value is None for value in measurements) and not all(
            value is None for value in measurements
        ):
            raise ValueError("post-escape measurements must be all known or all unknown")
        if all(value is None for value in measurements) and self.returned_inside_range:
            raise ValueError("an unknown post-escape history cannot contain a range return")
        if self.highest_price is not None:
            if (
                self.lowest_price is None
                or self.maximum_favorable_excursion is None
                or self.maximum_adverse_excursion is None
            ):
                raise ValueError("post-escape measurements must be all known or all unknown")
            if self.highest_price < self.lowest_price:
                raise ValueError("highest_price must not be below lowest_price")
            if (
                self.maximum_favorable_excursion < 0
                or self.maximum_adverse_excursion < 0
            ):
                raise ValueError("post-escape excursions must be non-negative")
        if self.returned_inside_range != (self.first_return_inside_timestamp is not None):
            raise ValueError(
                "returned_inside_range must match first_return_inside_timestamp"
            )
        if self.first_return_inside_timestamp is not None:
            _require_timezone_aware(
                self.first_return_inside_timestamp,
                "first_return_inside_timestamp",
            )


@dataclass(frozen=True, slots=True)
class ORBBehaviorRecord:
    """Aggregates existing immutable ORB research outputs for one session."""

    opening_range: OpeningRange
    escape_event: ORBEscapeEvent | None
    post_escape_observation: ORBPostEscapeObservation | None
    behavior: ORBBehavior
    features: ORBFeatures


@dataclass(frozen=True, slots=True)
class ORBBehaviorStatistics:
    """Records immutable aggregate counts over completed ORB behavior records."""

    total_records: int
    no_escape_count: int
    escape_with_return_count: int
    escape_without_return_count: int
    upward_escape_count: int
    downward_escape_count: int
    returned_to_range_count: int


@dataclass(frozen=True, slots=True)
class ORBFeatureSummary:
    """Records exact descriptive values for one existing numeric ORB feature."""

    count: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    median: float | None

    def __post_init__(self) -> None:
        """Keep empty and observed numeric summaries internally consistent."""
        if type(self.count) is not int or self.count < 0:
            raise ValueError("count must be a non-negative integer")
        values = (self.minimum, self.maximum, self.mean, self.median)
        if self.count == 0:
            if any(value is not None for value in values):
                raise ValueError("an empty summary must not contain numeric values")
            return
        if any(value is None for value in values):
            raise ValueError("a non-empty summary requires every numeric value")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            for value in values
        ):
            raise ValueError("summary values must be finite numeric values")
        if self.minimum is not None and self.maximum is not None:
            if self.minimum > self.maximum:
                raise ValueError("minimum must not exceed maximum")


@dataclass(frozen=True, slots=True)
class ORBFeatureSummaryDifference:
    """Records absolute differences between two existing feature summaries."""

    count_difference: int
    minimum_difference: float | None
    maximum_difference: float | None
    mean_difference: float | None
    median_difference: float | None

    def __post_init__(self) -> None:
        """Require finite, non-negative observed differences without coercion."""
        if type(self.count_difference) is not int or self.count_difference < 0:
            raise ValueError("count_difference must be a non-negative integer")
        for value in (
            self.minimum_difference,
            self.maximum_difference,
            self.mean_difference,
            self.median_difference,
        ):
            if value is None:
                continue
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or value < 0
            ):
                raise ValueError(
                    "feature summary differences must be finite non-negative values"
                )


class ORBHypothesisMetric(str, Enum):
    """Identifies the existing descriptive fact evaluated by a hypothesis."""

    RANGE_SIZE_MEAN = "RANGE_SIZE_MEAN"
    RANGE_SIZE_MEDIAN = "RANGE_SIZE_MEDIAN"
    MAXIMUM_FAVORABLE_EXCURSION_MEAN = "MAXIMUM_FAVORABLE_EXCURSION_MEAN"
    MAXIMUM_FAVORABLE_EXCURSION_MEDIAN = "MAXIMUM_FAVORABLE_EXCURSION_MEDIAN"
    MAXIMUM_ADVERSE_EXCURSION_MEAN = "MAXIMUM_ADVERSE_EXCURSION_MEAN"
    MAXIMUM_ADVERSE_EXCURSION_MEDIAN = "MAXIMUM_ADVERSE_EXCURSION_MEDIAN"
    BEHAVIOR_PROPORTION = "BEHAVIOR_PROPORTION"
    ESCAPE_DIRECTION_PROPORTION = "ESCAPE_DIRECTION_PROPORTION"
    RETURN_TO_RANGE_PROPORTION = "RETURN_TO_RANGE_PROPORTION"


class ORBHypothesisRelation(str, Enum):
    """Identifies the supported deterministic relation between two values."""

    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    EQUAL = "EQUAL"


class ORBHypothesisOutcome(str, Enum):
    """Identifies whether canonical observations satisfy a hypothesis."""

    SUPPORTED = "SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    NOT_EVALUABLE = "NOT_EVALUABLE"


class ORBHypothesisNotEvaluableReason(str, Enum):
    """Identifies which canonical observation is unavailable for evaluation."""

    LEFT_VALUE_UNAVAILABLE = "LEFT_VALUE_UNAVAILABLE"
    RIGHT_VALUE_UNAVAILABLE = "RIGHT_VALUE_UNAVAILABLE"
    BOTH_VALUES_UNAVAILABLE = "BOTH_VALUES_UNAVAILABLE"


class ORBResearchFindingStatus(str, Enum):
    """Identifies the deterministic observation state of a research finding."""

    OBSERVED = "OBSERVED"
    NOT_OBSERVED = "NOT_OBSERVED"
    NOT_EVALUABLE = "NOT_EVALUABLE"


class ORBStatisticalValidationStatus(str, Enum):
    """Identifies the request state for future statistical validation only."""

    NOT_REQUESTED = "NOT_REQUESTED"
    PENDING = "PENDING"


class ORBStatisticalValidationLifecycleStatus(str, Enum):
    """Identifies the lifecycle stage of one statistical validation record."""

    PENDING = "PENDING"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    COMPLETE = "COMPLETE"


class ORBStatisticalTestFamily(str, Enum):
    """Identifies the broad family of a planned statistical method."""

    PARAMETRIC = "PARAMETRIC"
    NON_PARAMETRIC = "NON_PARAMETRIC"
    CATEGORICAL = "CATEGORICAL"
    RESAMPLING = "RESAMPLING"


class ORBStatisticalTestIdentifier(str, Enum):
    """Identifies a planned statistical method without executing it."""

    WELCH_T_TEST = "WELCH_T_TEST"
    MANN_WHITNEY_U = "MANN_WHITNEY_U"
    CHI_SQUARE = "CHI_SQUARE"
    FISHER_EXACT = "FISHER_EXACT"
    PERMUTATION_TEST = "PERMUTATION_TEST"
    BOOTSTRAP = "BOOTSTRAP"


class ORBStatisticalValidationNotEvaluableReason(str, Enum):
    """Identifies a stable framework-level reason validation cannot proceed."""

    FINDING_NOT_ELIGIBLE = "FINDING_NOT_ELIGIBLE"
    INSUFFICIENT_OBSERVATIONS = "INSUFFICIENT_OBSERVATIONS"
    MISSING_OBSERVATIONS = "MISSING_OBSERVATIONS"
    UNSUPPORTED_METRIC = "UNSUPPORTED_METRIC"
    TEST_NOT_IMPLEMENTED = "TEST_NOT_IMPLEMENTED"


@dataclass(frozen=True, slots=True)
class ORBBehaviorHypothesis:
    """Declares one deterministic relation over existing descriptive facts."""

    metric: ORBHypothesisMetric
    relation: ORBHypothesisRelation
    category: ORBBehaviorKind | ORBEscapeDirection | bool | None = None
    minimum_absolute_difference: float = 0.0

    def __post_init__(self) -> None:
        """Require explicit supported metrics, relations, categories, and bounds."""
        if not isinstance(self.metric, ORBHypothesisMetric):
            raise TypeError("metric must be an ORBHypothesisMetric")
        if not isinstance(self.relation, ORBHypothesisRelation):
            raise TypeError("relation must be an ORBHypothesisRelation")
        _validate_hypothesis_category(self.metric, self.category)
        if (
            isinstance(self.minimum_absolute_difference, bool)
            or not isinstance(self.minimum_absolute_difference, (int, float))
            or not isfinite(self.minimum_absolute_difference)
            or self.minimum_absolute_difference < 0
        ):
            raise ValueError(
                "minimum_absolute_difference must be a finite non-negative number"
            )
        if (
            self.relation is ORBHypothesisRelation.EQUAL
            and self.minimum_absolute_difference != 0
        ):
            raise ValueError(
                "an EQUAL hypothesis requires zero minimum_absolute_difference"
            )


@dataclass(frozen=True, slots=True)
class ORBBehaviorHypothesisEvaluation:
    """Records the deterministic result of evaluating one atlas comparison."""

    hypothesis: ORBBehaviorHypothesis
    comparison: "ORBBehaviorComparison"
    left_value: float | None
    right_value: float | None
    signed_difference: float | None
    absolute_difference: float | None
    outcome: ORBHypothesisOutcome
    not_evaluable_reason: ORBHypothesisNotEvaluableReason | None

    def __post_init__(self) -> None:
        """Keep observed values, difference facts, and outcome semantics aligned."""
        if not isinstance(self.hypothesis, ORBBehaviorHypothesis):
            raise TypeError("hypothesis must be an ORBBehaviorHypothesis")
        if not isinstance(self.comparison, ORBBehaviorComparison):
            raise TypeError("comparison must be an ORBBehaviorComparison")
        if not isinstance(self.outcome, ORBHypothesisOutcome):
            raise TypeError("outcome must be an ORBHypothesisOutcome")
        if self.not_evaluable_reason is not None and not isinstance(
            self.not_evaluable_reason,
            ORBHypothesisNotEvaluableReason,
        ):
            raise TypeError(
                "not_evaluable_reason must be an ORBHypothesisNotEvaluableReason"
            )
        _validate_optional_finite_value(self.left_value, "left_value")
        _validate_optional_finite_value(self.right_value, "right_value")
        _validate_optional_finite_value(
            self.signed_difference,
            "signed_difference",
        )
        _validate_optional_finite_value(
            self.absolute_difference,
            "absolute_difference",
        )
        if self.absolute_difference is not None and self.absolute_difference < 0:
            raise ValueError("absolute_difference must be non-negative")
        if self.outcome is ORBHypothesisOutcome.NOT_EVALUABLE:
            if self.not_evaluable_reason is None:
                raise ValueError("NOT_EVALUABLE requires a stable reason")
            if self.signed_difference is not None or self.absolute_difference is not None:
                raise ValueError("NOT_EVALUABLE cannot contain difference values")
            _validate_not_evaluable_values(
                self.left_value,
                self.right_value,
                self.not_evaluable_reason,
            )
            return
        if self.not_evaluable_reason is not None:
            raise ValueError("an evaluable outcome cannot contain a reason")
        if self.left_value is None or self.right_value is None:
            raise ValueError("an evaluable outcome requires both observed values")
        if self.signed_difference is None or self.absolute_difference is None:
            raise ValueError("an evaluable outcome requires both difference values")
        if self.signed_difference != self.left_value - self.right_value:
            raise ValueError("signed_difference must match the observed values")
        if self.absolute_difference != abs(self.signed_difference):
            raise ValueError("absolute_difference must match signed_difference")


@dataclass(frozen=True, slots=True)
class ORBResearchFinding:
    """Compose one deterministic hypothesis evaluation for later validation."""

    evaluation: ORBBehaviorHypothesisEvaluation
    status: ORBResearchFindingStatus
    statistical_validation_status: ORBStatisticalValidationStatus
    note: str | None = None

    def __post_init__(self) -> None:
        """Require typed immutable evidence and an outcome-consistent status."""
        if not isinstance(self.evaluation, ORBBehaviorHypothesisEvaluation):
            raise TypeError("evaluation must be an ORBBehaviorHypothesisEvaluation")
        if not isinstance(self.status, ORBResearchFindingStatus):
            raise TypeError("status must be an ORBResearchFindingStatus")
        if not isinstance(
            self.statistical_validation_status,
            ORBStatisticalValidationStatus,
        ):
            raise TypeError(
                "statistical_validation_status must be an "
                "ORBStatisticalValidationStatus"
            )
        if self.note is not None and not isinstance(self.note, str):
            raise TypeError("note must be a string or None")
        expected_status = _finding_status_for_outcome(self.evaluation.outcome)
        if self.status is not expected_status:
            raise ValueError("status must match the evaluation outcome")
        if (
            self.statistical_validation_status
            is ORBStatisticalValidationStatus.PENDING
            and not self.is_eligible_for_statistical_validation
        ):
            raise ValueError("only observed findings can request statistical validation")

    @property
    def is_eligible_for_statistical_validation(self) -> bool:
        """Return whether this observed deterministic result may be validated later."""
        return self.status is ORBResearchFindingStatus.OBSERVED


@dataclass(frozen=True, slots=True)
class ORBStatisticalEvidence:
    """Retain common metadata for one future completed statistical procedure."""

    test_identifier: ORBStatisticalTestIdentifier
    test_family: ORBStatisticalTestFamily
    left_sample_size: int
    right_sample_size: int
    note: str | None = None

    def __post_init__(self) -> None:
        """Require typed test metadata and explicit non-negative sample sizes."""
        if not isinstance(self.test_identifier, ORBStatisticalTestIdentifier):
            raise TypeError("test_identifier must be an ORBStatisticalTestIdentifier")
        if not isinstance(self.test_family, ORBStatisticalTestFamily):
            raise TypeError("test_family must be an ORBStatisticalTestFamily")
        for sample_size, field_name in (
            (self.left_sample_size, "left_sample_size"),
            (self.right_sample_size, "right_sample_size"),
        ):
            if type(sample_size) is not int or sample_size < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if self.note is not None and not isinstance(self.note, str):
            raise TypeError("note must be a string or None")


@dataclass(frozen=True, slots=True)
class ORBStatisticalValidation:
    """Compose a requested research finding with its statistical lifecycle state."""

    finding: ORBResearchFinding
    lifecycle_status: ORBStatisticalValidationLifecycleStatus
    evidence: ORBStatisticalEvidence | None = None
    not_evaluable_reason: ORBStatisticalValidationNotEvaluableReason | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        """Require a requested eligible finding and a coherent lifecycle state."""
        if not isinstance(self.finding, ORBResearchFinding):
            raise TypeError("finding must be an ORBResearchFinding")
        if not isinstance(
            self.lifecycle_status,
            ORBStatisticalValidationLifecycleStatus,
        ):
            raise TypeError(
                "lifecycle_status must be an ORBStatisticalValidationLifecycleStatus"
            )
        if self.evidence is not None and not isinstance(
            self.evidence,
            ORBStatisticalEvidence,
        ):
            raise TypeError("evidence must be an ORBStatisticalEvidence or None")
        if self.not_evaluable_reason is not None and not isinstance(
            self.not_evaluable_reason,
            ORBStatisticalValidationNotEvaluableReason,
        ):
            raise TypeError(
                "not_evaluable_reason must be an "
                "ORBStatisticalValidationNotEvaluableReason or None"
            )
        if self.note is not None and not isinstance(self.note, str):
            raise TypeError("note must be a string or None")
        if not self.finding.is_eligible_for_statistical_validation:
            raise ValueError("finding must be eligible for statistical validation")
        if (
            self.finding.statistical_validation_status
            is not ORBStatisticalValidationStatus.PENDING
        ):
            raise ValueError("finding must have a pending statistical validation request")
        _validate_statistical_validation_state(
            self.lifecycle_status,
            self.evidence,
            self.not_evaluable_reason,
        )

    @property
    def is_pending(self) -> bool:
        """Return whether no statistical evidence has yet been attached."""
        return self.lifecycle_status is ORBStatisticalValidationLifecycleStatus.PENDING

    @property
    def is_complete(self) -> bool:
        """Return whether canonical statistical evidence has been attached."""
        return self.lifecycle_status is ORBStatisticalValidationLifecycleStatus.COMPLETE

    @property
    def is_not_evaluable(self) -> bool:
        """Return whether validation cannot proceed with this framework state."""
        return (
            self.lifecycle_status
            is ORBStatisticalValidationLifecycleStatus.NOT_EVALUABLE
        )

    @property
    def has_evidence(self) -> bool:
        """Return whether this lifecycle state retains completed evidence metadata."""
        return self.evidence is not None


@dataclass(frozen=True, slots=True)
class ORBBehaviorDescriptiveStatistics:
    """Combines existing categorical facts with numeric summaries of stored features."""

    categorical_counts: ORBBehaviorStatistics
    categorical_distributions: "ORBBehaviorDistributions"
    behavior_proportions: Mapping[ORBBehaviorKind, float]
    escape_direction_proportions: Mapping[ORBEscapeDirection, float]
    return_to_range_proportions: Mapping[bool, float]
    range_size: ORBFeatureSummary
    maximum_favorable_excursion: ORBFeatureSummary
    maximum_adverse_excursion: ORBFeatureSummary

    def __post_init__(self) -> None:
        """Defensively retain immutable proportion mappings and typed child results."""
        if not isinstance(self.categorical_counts, ORBBehaviorStatistics):
            raise TypeError("categorical_counts must be an ORBBehaviorStatistics")
        if not isinstance(self.categorical_distributions, ORBBehaviorDistributions):
            raise TypeError(
                "categorical_distributions must be an ORBBehaviorDistributions"
            )
        for summary in (
            self.range_size,
            self.maximum_favorable_excursion,
            self.maximum_adverse_excursion,
        ):
            if not isinstance(summary, ORBFeatureSummary):
                raise TypeError("numeric summaries must be ORBFeatureSummary values")
        object.__setattr__(
            self,
            "behavior_proportions",
            _freeze_proportions(
                self.behavior_proportions,
                ORBBehaviorKind,
                "behavior_proportions",
            ),
        )
        object.__setattr__(
            self,
            "escape_direction_proportions",
            _freeze_proportions(
                self.escape_direction_proportions,
                ORBEscapeDirection,
                "escape_direction_proportions",
            ),
        )
        object.__setattr__(
            self,
            "return_to_range_proportions",
            _freeze_proportions(
                self.return_to_range_proportions,
                bool,
                "return_to_range_proportions",
            ),
        )


@dataclass(frozen=True, slots=True)
class ORBBehaviorComparison:
    """Compares two immutable atlas subsets through existing descriptive facts."""

    left_statistics: ORBBehaviorDescriptiveStatistics
    right_statistics: ORBBehaviorDescriptiveStatistics
    range_size_difference: ORBFeatureSummaryDifference
    maximum_favorable_excursion_difference: ORBFeatureSummaryDifference
    maximum_adverse_excursion_difference: ORBFeatureSummaryDifference

    def __post_init__(self) -> None:
        """Require typed immutable summaries without recalculating either side."""
        if not isinstance(self.left_statistics, ORBBehaviorDescriptiveStatistics):
            raise TypeError("left_statistics must be ORBBehaviorDescriptiveStatistics")
        if not isinstance(self.right_statistics, ORBBehaviorDescriptiveStatistics):
            raise TypeError("right_statistics must be ORBBehaviorDescriptiveStatistics")
        for difference in (
            self.range_size_difference,
            self.maximum_favorable_excursion_difference,
            self.maximum_adverse_excursion_difference,
        ):
            if not isinstance(difference, ORBFeatureSummaryDifference):
                raise TypeError(
                    "numeric differences must be ORBFeatureSummaryDifference values"
                )


@dataclass(frozen=True, slots=True)
class ORBBehaviorDistributions:
    """Records immutable frequency maps for existing ORB behavior categories."""

    behavior_distribution: Mapping[ORBBehaviorKind, int]
    escape_direction_distribution: Mapping[ORBEscapeDirection, int]
    return_to_range_distribution: Mapping[bool, int]

    def __post_init__(self) -> None:
        """Defensively retain read-only observed-category frequency mappings."""
        object.__setattr__(
            self,
            "behavior_distribution",
            _freeze_distribution(
                self.behavior_distribution,
                ORBBehaviorKind,
                "behavior_distribution",
            ),
        )
        object.__setattr__(
            self,
            "escape_direction_distribution",
            _freeze_distribution(
                self.escape_direction_distribution,
                ORBEscapeDirection,
                "escape_direction_distribution",
            ),
        )
        object.__setattr__(
            self,
            "return_to_range_distribution",
            _freeze_distribution(
                self.return_to_range_distribution,
                bool,
                "return_to_range_distribution",
            ),
        )


@dataclass(frozen=True, slots=True)
class ORBBehaviorAtlas:
    """Represents an ordered immutable in-memory collection of behavior records."""

    records: tuple[ORBBehaviorRecord, ...]

    def __iter__(self) -> Iterator[ORBBehaviorRecord]:
        """Iterate over records in their supplied canonical order."""
        return iter(self.records)

    def __len__(self) -> int:
        """Return the number of records held by this atlas."""
        return len(self.records)

    def __getitem__(self, index: int) -> ORBBehaviorRecord:
        """Return one record by its zero-based canonical position."""
        return self.records[index]

    def by_behavior(self, behavior: ORBBehaviorKind) -> "ORBBehaviorAtlas":
        """Return records whose existing behavior matches ``behavior``.

        The returned immutable atlas preserves canonical record order and exact
        record references. It performs no classification or market analysis.

        Args:
            behavior: Existing behavior kind to retain.

        Raises:
            TypeError: If ``behavior`` is not an ``ORBBehaviorKind``.
        """
        if not isinstance(behavior, ORBBehaviorKind):
            raise TypeError("behavior must be an ORBBehaviorKind.")
        return ORBBehaviorAtlas(
            records=tuple(
                record for record in self.records if record.behavior.kind is behavior
            )
        )

    def by_escape_direction(
        self,
        direction: ORBEscapeDirection,
    ) -> "ORBBehaviorAtlas":
        """Return records whose existing escape direction matches ``direction``.

        No-escape records do not match because their existing escape event is
        absent. The returned immutable atlas preserves record order and
        references without deriving a direction.

        Args:
            direction: Existing escape direction to retain.

        Raises:
            TypeError: If ``direction`` is not an ``ORBEscapeDirection``.
        """
        if not isinstance(direction, ORBEscapeDirection):
            raise TypeError("direction must be an ORBEscapeDirection.")
        return ORBBehaviorAtlas(
            records=tuple(
                record
                for record in self.records
                if (
                    record.escape_event is not None
                    and record.escape_event.direction is direction
                )
            )
        )

    def by_return_to_range(self, returned: bool) -> "ORBBehaviorAtlas":
        """Return escaped records with the existing requested return fact.

        No-escape records have no return fact and therefore never match. The
        returned immutable atlas preserves record order and references without
        observing or recalculating post-escape market data.

        Args:
            returned: Existing return-to-range fact to retain.

        Raises:
            TypeError: If ``returned`` is not a boolean.
        """
        if not isinstance(returned, bool):
            raise TypeError("returned must be a bool.")
        return ORBBehaviorAtlas(
            records=tuple(
                record
                for record in self.records
                if (
                    record.post_escape_observation is not None
                    and record.post_escape_observation.returned_inside_range is returned
                )
            )
        )

    def filter(
        self,
        *,
        behavior: ORBBehaviorKind | None = None,
        escape_direction: ORBEscapeDirection | None = None,
        returned_to_range: bool | None = None,
    ) -> "ORBBehaviorAtlas":
        """Return records matching every supplied existing query criterion.

        Omitted criteria are ignored. The returned immutable atlas retains
        matching records in their canonical order and by exact reference; it
        neither derives nor modifies any research fact.

        Args:
            behavior: Existing behavior kind to retain, if supplied.
            escape_direction: Existing escape direction to retain, if supplied.
            returned_to_range: Existing return fact to retain, if supplied.

        Raises:
            TypeError: If a supplied criterion has an unsupported type.
        """
        if behavior is not None and not isinstance(behavior, ORBBehaviorKind):
            raise TypeError("behavior must be an ORBBehaviorKind or None.")
        if escape_direction is not None and not isinstance(
            escape_direction,
            ORBEscapeDirection,
        ):
            raise TypeError("escape_direction must be an ORBEscapeDirection or None.")
        if returned_to_range is not None and not isinstance(returned_to_range, bool):
            raise TypeError("returned_to_range must be a bool or None.")

        return ORBBehaviorAtlas(
            records=tuple(
                record
                for record in self.records
                if (
                    behavior is None or record.behavior.kind is behavior
                )
                and (
                    escape_direction is None
                    or (
                        record.escape_event is not None
                        and record.escape_event.direction is escape_direction
                    )
                )
                and (
                    returned_to_range is None
                    or (
                        record.post_escape_observation is not None
                        and (
                            record.post_escape_observation.returned_inside_range
                            is returned_to_range
                        )
                    )
                )
            )
        )


@dataclass(frozen=True, slots=True)
class ORBBehaviorAtlasGroups:
    """Represents immutable key-to-atlas groups of existing behavior records."""

    groups: Mapping[
        ORBBehaviorKind | ORBEscapeDirection | bool,
        ORBBehaviorAtlas,
    ]

    def __post_init__(self) -> None:
        """Defensively retain a read-only mapping of supported group values."""
        if not isinstance(self.groups, Mapping):
            raise TypeError("groups must be a mapping of supported keys to atlases.")

        immutable_groups: dict[
            ORBBehaviorKind | ORBEscapeDirection | bool,
            ORBBehaviorAtlas,
        ] = {}
        for key, atlas in self.groups.items():
            if not isinstance(key, (ORBBehaviorKind, ORBEscapeDirection, bool)):
                raise TypeError("groups must use supported behavior atlas keys.")
            if not isinstance(atlas, ORBBehaviorAtlas):
                raise TypeError("groups must contain only ORBBehaviorAtlas values.")
            immutable_groups[key] = atlas

        object.__setattr__(self, "groups", MappingProxyType(immutable_groups))


@dataclass(frozen=True, slots=True)
class ORBSession:
    """Associates one canonical session with its observed opening range."""

    session: Session
    opening_range: OpeningRange


def _require_timezone_aware(timestamp: datetime, field_name: str) -> None:
    """Reject timestamps that cannot identify a canonical timezone instant."""
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _freeze_distribution(
    distribution: Mapping[_DistributionCategory, int],
    category_type: type[_DistributionCategory],
    field_name: str,
) -> Mapping[_DistributionCategory, int]:
    """Return a read-only non-empty-count mapping of one supported category type."""
    if not isinstance(distribution, Mapping):
        raise TypeError(f"{field_name} must be a mapping.")

    immutable_distribution: dict[_DistributionCategory, int] = {}
    for category, count in distribution.items():
        if not isinstance(category, category_type):
            raise TypeError(f"{field_name} contains an unsupported category.")
        if type(count) is not int or count <= 0:
            raise ValueError(f"{field_name} counts must be positive integers.")
        immutable_distribution[category] = count

    return MappingProxyType(immutable_distribution)


def _freeze_proportions(
    proportions: Mapping[_DistributionCategory, float],
    category_type: type[_DistributionCategory],
    field_name: str,
) -> Mapping[_DistributionCategory, float]:
    """Return an immutable supported-category proportion mapping in input order."""
    if not isinstance(proportions, Mapping):
        raise TypeError(f"{field_name} must be a mapping.")

    immutable_proportions: dict[_DistributionCategory, float] = {}
    for category, proportion in proportions.items():
        if not isinstance(category, category_type):
            raise TypeError(f"{field_name} contains an unsupported category.")
        if (
            isinstance(proportion, bool)
            or not isinstance(proportion, (int, float))
            or not isfinite(proportion)
            or proportion < 0.0
            or proportion > 1.0
        ):
            raise ValueError(f"{field_name} values must be finite proportions.")
        immutable_proportions[category] = proportion

    return MappingProxyType(immutable_proportions)


def _validate_hypothesis_category(
    metric: ORBHypothesisMetric,
    category: ORBBehaviorKind | ORBEscapeDirection | bool | None,
) -> None:
    """Require only the existing category type associated with a metric."""
    numeric_metrics = (
        ORBHypothesisMetric.RANGE_SIZE_MEAN,
        ORBHypothesisMetric.RANGE_SIZE_MEDIAN,
        ORBHypothesisMetric.MAXIMUM_FAVORABLE_EXCURSION_MEAN,
        ORBHypothesisMetric.MAXIMUM_FAVORABLE_EXCURSION_MEDIAN,
        ORBHypothesisMetric.MAXIMUM_ADVERSE_EXCURSION_MEAN,
        ORBHypothesisMetric.MAXIMUM_ADVERSE_EXCURSION_MEDIAN,
    )
    if metric in numeric_metrics:
        if category is not None:
            raise ValueError("numeric hypothesis metrics must not specify a category")
        return
    if metric is ORBHypothesisMetric.BEHAVIOR_PROPORTION:
        if not isinstance(category, ORBBehaviorKind):
            raise TypeError("BEHAVIOR_PROPORTION requires an ORBBehaviorKind category")
        return
    if metric is ORBHypothesisMetric.ESCAPE_DIRECTION_PROPORTION:
        if not isinstance(category, ORBEscapeDirection):
            raise TypeError(
                "ESCAPE_DIRECTION_PROPORTION requires an ORBEscapeDirection category"
            )
        return
    if metric is ORBHypothesisMetric.RETURN_TO_RANGE_PROPORTION:
        if type(category) is not bool:
            raise TypeError("RETURN_TO_RANGE_PROPORTION requires a bool category")
        return
    raise ValueError("metric is unsupported")


def _finding_status_for_outcome(
    outcome: ORBHypothesisOutcome,
) -> ORBResearchFindingStatus:
    """Map one completed deterministic outcome to its finding status."""
    if outcome is ORBHypothesisOutcome.SUPPORTED:
        return ORBResearchFindingStatus.OBSERVED
    if outcome is ORBHypothesisOutcome.NOT_SUPPORTED:
        return ORBResearchFindingStatus.NOT_OBSERVED
    if outcome is ORBHypothesisOutcome.NOT_EVALUABLE:
        return ORBResearchFindingStatus.NOT_EVALUABLE
    raise ValueError("outcome is unsupported")


def _validate_statistical_validation_state(
    lifecycle_status: ORBStatisticalValidationLifecycleStatus,
    evidence: ORBStatisticalEvidence | None,
    not_evaluable_reason: ORBStatisticalValidationNotEvaluableReason | None,
) -> None:
    """Require only the evidence and reason combination for one lifecycle state."""
    if lifecycle_status is ORBStatisticalValidationLifecycleStatus.PENDING:
        if evidence is not None or not_evaluable_reason is not None:
            raise ValueError("PENDING validation must not contain evidence or a reason")
        return
    if lifecycle_status is ORBStatisticalValidationLifecycleStatus.NOT_EVALUABLE:
        if evidence is not None or not_evaluable_reason is None:
            raise ValueError(
                "NOT_EVALUABLE validation requires a reason and no evidence"
            )
        return
    if lifecycle_status is ORBStatisticalValidationLifecycleStatus.COMPLETE:
        if evidence is None or not_evaluable_reason is not None:
            raise ValueError(
                "COMPLETE validation requires evidence and no not-evaluable reason"
            )
        return
    raise ValueError("lifecycle_status is unsupported")


def _validate_optional_finite_value(value: float | None, field_name: str) -> None:
    """Reject non-numeric, boolean, and non-finite observed evaluation values."""
    if value is None:
        return
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
    ):
        raise ValueError(f"{field_name} must be a finite numeric value or None")


def _validate_not_evaluable_values(
    left_value: float | None,
    right_value: float | None,
    reason: ORBHypothesisNotEvaluableReason,
) -> None:
    """Require the stable unavailable reason to match the retained observations."""
    if left_value is None and right_value is None:
        expected = ORBHypothesisNotEvaluableReason.BOTH_VALUES_UNAVAILABLE
    elif left_value is None:
        expected = ORBHypothesisNotEvaluableReason.LEFT_VALUE_UNAVAILABLE
    elif right_value is None:
        expected = ORBHypothesisNotEvaluableReason.RIGHT_VALUE_UNAVAILABLE
    else:
        raise ValueError("NOT_EVALUABLE requires at least one unavailable value")
    if reason is not expected:
        raise ValueError("not_evaluable_reason must match unavailable observations")
