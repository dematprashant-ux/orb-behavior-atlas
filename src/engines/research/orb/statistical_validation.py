"""Pure lifecycle construction for immutable ORB statistical validation facts."""

from src.engines.research.orb.models import (
    ORBResearchFinding,
    ORBStatisticalEvidence,
    ORBStatisticalValidation,
    ORBStatisticalValidationLifecycleStatus,
    ORBStatisticalValidationNotEvaluableReason,
    ORBStatisticalValidationStatus,
)

__all__ = [
    "complete_statistical_validation",
    "create_statistical_validation",
    "mark_statistical_validation_not_evaluable",
]


def create_statistical_validation(
    finding: ORBResearchFinding,
) -> ORBStatisticalValidation:
    """Create a pending lifecycle record for one explicitly requested finding."""
    if not isinstance(finding, ORBResearchFinding):
        raise TypeError("finding must be an ORBResearchFinding")
    if not finding.is_eligible_for_statistical_validation:
        raise ValueError("finding must be eligible for statistical validation")
    if (
        finding.statistical_validation_status
        is not ORBStatisticalValidationStatus.PENDING
    ):
        raise ValueError("finding must have a pending statistical validation request")
    return ORBStatisticalValidation(
        finding=finding,
        lifecycle_status=ORBStatisticalValidationLifecycleStatus.PENDING,
    )


def mark_statistical_validation_not_evaluable(
    validation: ORBStatisticalValidation,
    reason: ORBStatisticalValidationNotEvaluableReason,
    *,
    note: str | None = None,
) -> ORBStatisticalValidation:
    """Return a terminal not-evaluable record from a pending lifecycle record."""
    _require_pending_validation(validation)
    if not isinstance(reason, ORBStatisticalValidationNotEvaluableReason):
        raise TypeError(
            "reason must be an ORBStatisticalValidationNotEvaluableReason"
        )
    return ORBStatisticalValidation(
        finding=validation.finding,
        lifecycle_status=ORBStatisticalValidationLifecycleStatus.NOT_EVALUABLE,
        not_evaluable_reason=reason,
        note=note,
    )


def complete_statistical_validation(
    validation: ORBStatisticalValidation,
    evidence: ORBStatisticalEvidence,
) -> ORBStatisticalValidation:
    """Return a terminal complete record from a pending lifecycle record."""
    _require_pending_validation(validation)
    if not isinstance(evidence, ORBStatisticalEvidence):
        raise TypeError("evidence must be an ORBStatisticalEvidence")
    return ORBStatisticalValidation(
        finding=validation.finding,
        lifecycle_status=ORBStatisticalValidationLifecycleStatus.COMPLETE,
        evidence=evidence,
    )


def _require_pending_validation(validation: ORBStatisticalValidation) -> None:
    """Reject invalid inputs and every transition from terminal lifecycle states."""
    if not isinstance(validation, ORBStatisticalValidation):
        raise TypeError("validation must be an ORBStatisticalValidation")
    if not validation.is_pending:
        raise ValueError("only pending statistical validations can transition")
