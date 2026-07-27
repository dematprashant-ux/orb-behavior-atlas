"""Contract tests for immutable findings from deterministic ORB hypotheses."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase
from unittest.mock import patch

from src.engines.research import (
    ORBBehaviorHypothesisEvaluation,
    ORBResearchFinding,
    ORBResearchFindingStatus,
    ORBStatisticalValidationStatus,
    create_research_finding,
    request_statistical_validation,
)
from src.engines.research.orb import findings
from src.engines.research.orb.models import ORBHypothesisMetric, ORBHypothesisRelation
from src.engines.research.orb.hypothesis import evaluate_behavior_hypothesis
from src.engines.research.orb.atlas import build_behavior_atlas
from tests.test_research_orb_hypothesis import _hypothesis, _range_atlas


class ORBResearchFindingTests(TestCase):
    """Verify stable finding composition without statistical or strategy behavior."""

    def test_supported_evaluation_creates_observed_eligible_finding(self) -> None:
        """Map completed deterministic support to an observed finding."""
        evaluation = _evaluation(4.0, 2.0)

        finding = create_research_finding(
            evaluation,
            note="Observed during high-volatility sessions.",
        )

        self.assertIs(finding.evaluation, evaluation)
        self.assertIs(finding.status, ORBResearchFindingStatus.OBSERVED)
        self.assertIs(
            finding.statistical_validation_status,
            ORBStatisticalValidationStatus.NOT_REQUESTED,
        )
        self.assertTrue(finding.is_eligible_for_statistical_validation)
        self.assertEqual(finding.note, "Observed during high-volatility sessions.")

    def test_evaluation_outcomes_map_to_neutral_finding_statuses(self) -> None:
        """Preserve unsupported and unavailable outcomes without statistical labels."""
        cases = (
            (_evaluation(2.0, 4.0), ORBResearchFindingStatus.NOT_OBSERVED),
            (_not_evaluable_evaluation(), ORBResearchFindingStatus.NOT_EVALUABLE),
        )

        for evaluation, expected_status in cases:
            with self.subTest(outcome=evaluation.outcome):
                finding = create_research_finding(evaluation)
                self.assertIs(finding.status, expected_status)
                self.assertFalse(finding.is_eligible_for_statistical_validation)

    def test_requesting_validation_returns_pending_copy_without_mutation(self) -> None:
        """Keep evidence and note references while making an immutable request."""
        original = create_research_finding(_evaluation(4.0, 2.0), note="Reserve")

        pending = request_statistical_validation(original)

        self.assertIs(pending.evaluation, original.evaluation)
        self.assertEqual(pending.note, original.note)
        self.assertIs(
            original.statistical_validation_status,
            ORBStatisticalValidationStatus.NOT_REQUESTED,
        )
        self.assertIs(
            pending.statistical_validation_status,
            ORBStatisticalValidationStatus.PENDING,
        )
        self.assertEqual(pending, request_statistical_validation(pending))

    def test_ineligible_findings_reject_statistical_validation_requests(self) -> None:
        """Do not request future validation for unsupported or unavailable facts."""
        for evaluation in (_evaluation(2.0, 4.0), _not_evaluable_evaluation()):
            with self.subTest(outcome=evaluation.outcome):
                with self.assertRaisesRegex(ValueError, "eligible"):
                    request_statistical_validation(create_research_finding(evaluation))

    def test_model_rejects_invalid_intrinsic_construction(self) -> None:
        """Require canonical evidence, matching status, and a descriptive string."""
        evaluation = _evaluation(4.0, 2.0)
        with self.assertRaises(TypeError):
            create_research_finding("evaluation")  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "match"):
            ORBResearchFinding(
                evaluation=evaluation,
                status=ORBResearchFindingStatus.NOT_OBSERVED,
                statistical_validation_status=ORBStatisticalValidationStatus.NOT_REQUESTED,
            )
        with self.assertRaisesRegex(TypeError, "note"):
            create_research_finding(evaluation, note=1)  # type: ignore[arg-type]

    def test_finding_is_immutable_deterministic_and_publicly_exported(self) -> None:
        """Expose frozen value semantics without copied evaluation facts."""
        evaluation = _evaluation(4.0, 2.0)
        first = create_research_finding(evaluation)
        second = create_research_finding(evaluation)

        self.assertIsInstance(first, ORBResearchFinding)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        with self.assertRaises(FrozenInstanceError):
            first.note = "mutated"

    def test_finding_creation_never_recomputes_existing_evaluation(self) -> None:
        """Compose the supplied canonical evidence without comparing atlases again."""
        evaluation = _evaluation(4.0, 2.0)
        with patch.object(
            findings,
            "_status_for_evaluation",
            wraps=findings._status_for_evaluation,
        ) as mapper:
            finding = create_research_finding(evaluation)

        self.assertIs(finding.evaluation, evaluation)
        self.assertEqual(mapper.call_count, 1)


def _evaluation(left: float, right: float) -> ORBBehaviorHypothesisEvaluation:
    """Build one complete canonical range-size evaluation using public behavior."""
    return evaluate_behavior_hypothesis(
        _hypothesis(
            ORBHypothesisMetric.RANGE_SIZE_MEAN,
            ORBHypothesisRelation.GREATER_THAN,
        ),
        _range_atlas(left),
        _range_atlas(right),
    )


def _not_evaluable_evaluation() -> ORBBehaviorHypothesisEvaluation:
    """Build canonical unavailable evidence without fabricating an observation."""
    return evaluate_behavior_hypothesis(
        _hypothesis(
            ORBHypothesisMetric.RANGE_SIZE_MEAN,
            ORBHypothesisRelation.GREATER_THAN,
        ),
        build_behavior_atlas(()),
        build_behavior_atlas(()),
    )
