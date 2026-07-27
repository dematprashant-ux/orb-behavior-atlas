"""Pure construction and state transition for deterministic ORB findings."""

from src.engines.research.orb.models import (
    ORBBehaviorHypothesisEvaluation,
    ORBHypothesisOutcome,
    ORBResearchFinding,
    ORBResearchFindingStatus,
    ORBStatisticalValidationStatus,
)

__all__ = ["create_research_finding", "request_statistical_validation"]


def create_research_finding(
    evaluation: ORBBehaviorHypothesisEvaluation,
    *,
    note: str | None = None,
) -> ORBResearchFinding:
    """Compose a finding from completed deterministic hypothesis evidence."""
    if not isinstance(evaluation, ORBBehaviorHypothesisEvaluation):
        raise TypeError("evaluation must be an ORBBehaviorHypothesisEvaluation")
    return ORBResearchFinding(
        evaluation=evaluation,
        status=_status_for_evaluation(evaluation),
        statistical_validation_status=ORBStatisticalValidationStatus.NOT_REQUESTED,
        note=note,
    )


def request_statistical_validation(finding: ORBResearchFinding) -> ORBResearchFinding:
    """Return an eligible finding marked for future statistical validation.

    A request for an already pending eligible finding is idempotent and returns
    an equal immutable replacement rather than starting a validation process.
    """
    if not isinstance(finding, ORBResearchFinding):
        raise TypeError("finding must be an ORBResearchFinding")
    if not finding.is_eligible_for_statistical_validation:
        raise ValueError("only observed findings are eligible for statistical validation")
    return ORBResearchFinding(
        evaluation=finding.evaluation,
        status=finding.status,
        statistical_validation_status=ORBStatisticalValidationStatus.PENDING,
        note=finding.note,
    )


def _status_for_evaluation(
    evaluation: ORBBehaviorHypothesisEvaluation,
) -> ORBResearchFindingStatus:
    """Map only the completed deterministic evaluation outcome to a finding."""
    if evaluation.outcome is ORBHypothesisOutcome.SUPPORTED:
        return ORBResearchFindingStatus.OBSERVED
    if evaluation.outcome is ORBHypothesisOutcome.NOT_SUPPORTED:
        return ORBResearchFindingStatus.NOT_OBSERVED
    if evaluation.outcome is ORBHypothesisOutcome.NOT_EVALUABLE:
        return ORBResearchFindingStatus.NOT_EVALUABLE
    raise ValueError("evaluation outcome is unsupported")
