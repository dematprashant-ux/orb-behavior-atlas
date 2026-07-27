"""Contract tests for immutable ORB statistical-validation lifecycle records."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.research import (
    ORBResearchFinding,
    ORBStatisticalEvidence,
    ORBStatisticalTestFamily,
    ORBStatisticalTestIdentifier,
    ORBStatisticalValidation,
    ORBStatisticalValidationLifecycleStatus,
    ORBStatisticalValidationNotEvaluableReason,
    complete_statistical_validation,
    create_research_finding,
    create_statistical_validation,
    mark_statistical_validation_not_evaluable,
    request_statistical_validation,
)
from src.engines.research.orb.atlas import build_behavior_atlas
from src.engines.research.orb.hypothesis import evaluate_behavior_hypothesis
from src.engines.research.orb.models import (
    ORBHypothesisMetric,
    ORBHypothesisRelation,
)
from tests.test_research_orb_hypothesis import _hypothesis, _range_atlas


class ORBStatisticalValidationTests(TestCase):
    """Verify lifecycle composition without statistical calculation or interpretation."""

    def test_creates_pending_validation_from_requested_eligible_finding(self) -> None:
        """Retain the exact requested finding with no evidence or unavailable reason."""
        finding = _pending_finding()

        validation = create_statistical_validation(finding)

        self.assertIs(validation.finding, finding)
        self.assertIs(
            validation.lifecycle_status,
            ORBStatisticalValidationLifecycleStatus.PENDING,
        )
        self.assertIsNone(validation.evidence)
        self.assertIsNone(validation.not_evaluable_reason)
        self.assertTrue(validation.is_pending)
        self.assertFalse(validation.is_complete)
        self.assertFalse(validation.is_not_evaluable)
        self.assertFalse(validation.has_evidence)

    def test_rejects_findings_without_eligible_pending_request(self) -> None:
        """Require R3.1 eligibility and an explicit pending request before creation."""
        not_requested = create_research_finding(_evaluation(4.0, 2.0))
        not_observed = create_research_finding(_evaluation(2.0, 4.0))
        unavailable = create_research_finding(_not_evaluable_evaluation())

        with self.assertRaisesRegex(ValueError, "pending"):
            create_statistical_validation(not_requested)
        with self.assertRaisesRegex(TypeError, "finding"):
            create_statistical_validation("finding")  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "eligible"):
            create_statistical_validation(not_observed)
        with self.assertRaisesRegex(ValueError, "eligible"):
            create_statistical_validation(unavailable)

    def test_evidence_retains_typed_metadata_and_accepts_zero_sample_sizes(self) -> None:
        """Store supplied framework metadata without deriving samples or results."""
        evidence = ORBStatisticalEvidence(
            test_identifier=ORBStatisticalTestIdentifier.WELCH_T_TEST,
            test_family=ORBStatisticalTestFamily.PARAMETRIC,
            left_sample_size=0,
            right_sample_size=0,
            note="Awaiting a future implementation.",
        )

        self.assertEqual(evidence.left_sample_size, 0)
        self.assertEqual(evidence.right_sample_size, 0)
        self.assertEqual(evidence.note, "Awaiting a future implementation.")
        with self.assertRaises(ValueError):
            ORBStatisticalEvidence(
                ORBStatisticalTestIdentifier.BOOTSTRAP,
                ORBStatisticalTestFamily.RESAMPLING,
                -1,
                1,
            )
        with self.assertRaises(ValueError):
            ORBStatisticalEvidence(
                ORBStatisticalTestIdentifier.BOOTSTRAP,
                ORBStatisticalTestFamily.RESAMPLING,
                True,
                1,
            )

    def test_stable_test_enums_expose_only_planned_values(self) -> None:
        """Keep test identifiers and broad families deterministic and typed."""
        self.assertEqual(
            tuple(ORBStatisticalTestFamily),
            (
                ORBStatisticalTestFamily.PARAMETRIC,
                ORBStatisticalTestFamily.NON_PARAMETRIC,
                ORBStatisticalTestFamily.CATEGORICAL,
                ORBStatisticalTestFamily.RESAMPLING,
            ),
        )
        self.assertEqual(
            tuple(ORBStatisticalTestIdentifier),
            (
                ORBStatisticalTestIdentifier.WELCH_T_TEST,
                ORBStatisticalTestIdentifier.MANN_WHITNEY_U,
                ORBStatisticalTestIdentifier.CHI_SQUARE,
                ORBStatisticalTestIdentifier.FISHER_EXACT,
                ORBStatisticalTestIdentifier.PERMUTATION_TEST,
                ORBStatisticalTestIdentifier.BOOTSTRAP,
            ),
        )

    def test_marks_pending_validation_not_evaluable_without_mutating_original(self) -> None:
        """Attach only a stable reason and optional note to a terminal copy."""
        pending = create_statistical_validation(_pending_finding())

        result = mark_statistical_validation_not_evaluable(
            pending,
            ORBStatisticalValidationNotEvaluableReason.MISSING_OBSERVATIONS,
            note="Canonical observations are absent.",
        )

        self.assertIs(result.finding, pending.finding)
        self.assertIsNone(result.evidence)
        self.assertIs(
            result.not_evaluable_reason,
            ORBStatisticalValidationNotEvaluableReason.MISSING_OBSERVATIONS,
        )
        self.assertEqual(result.note, "Canonical observations are absent.")
        self.assertTrue(result.is_not_evaluable)
        self.assertTrue(pending.is_pending)

    def test_completes_pending_validation_with_exact_evidence(self) -> None:
        """Attach caller-supplied evidence metadata without calculating a result."""
        pending = create_statistical_validation(_pending_finding())
        evidence = _evidence()

        complete = complete_statistical_validation(pending, evidence)

        self.assertIs(complete.finding, pending.finding)
        self.assertIs(complete.evidence, evidence)
        self.assertIsNone(complete.not_evaluable_reason)
        self.assertTrue(complete.is_complete)
        self.assertTrue(complete.has_evidence)
        self.assertTrue(pending.is_pending)

    def test_model_rejects_contradictory_lifecycle_combinations(self) -> None:
        """Keep pending, unavailable, and complete states mutually coherent."""
        finding = _pending_finding()
        evidence = _evidence()
        reason = ORBStatisticalValidationNotEvaluableReason.TEST_NOT_IMPLEMENTED

        cases = (
            (ORBStatisticalValidationLifecycleStatus.PENDING, evidence, None),
            (ORBStatisticalValidationLifecycleStatus.NOT_EVALUABLE, None, None),
            (ORBStatisticalValidationLifecycleStatus.COMPLETE, None, None),
            (ORBStatisticalValidationLifecycleStatus.COMPLETE, evidence, reason),
        )
        for lifecycle_status, case_evidence, case_reason in cases:
            with self.subTest(lifecycle_status=lifecycle_status):
                with self.assertRaises(ValueError):
                    ORBStatisticalValidation(
                        finding,
                        lifecycle_status,
                        evidence=case_evidence,
                        not_evaluable_reason=case_reason,
                    )

    def test_terminal_validations_reject_every_further_transition(self) -> None:
        """Apply the documented terminal-state rejection policy deterministically."""
        pending = create_statistical_validation(_pending_finding())
        complete = complete_statistical_validation(pending, _evidence())
        unavailable = mark_statistical_validation_not_evaluable(
            pending,
            ORBStatisticalValidationNotEvaluableReason.TEST_NOT_IMPLEMENTED,
        )

        for terminal in (complete, unavailable):
            with self.subTest(lifecycle_status=terminal.lifecycle_status):
                with self.assertRaisesRegex(ValueError, "pending"):
                    complete_statistical_validation(terminal, _evidence())
                with self.assertRaisesRegex(ValueError, "pending"):
                    mark_statistical_validation_not_evaluable(
                        terminal,
                        ORBStatisticalValidationNotEvaluableReason.TEST_NOT_IMPLEMENTED,
                    )

    def test_models_are_immutable_deterministic_and_publicly_exported(self) -> None:
        """Expose frozen equality and repr semantics without mutable metadata."""
        evidence = _evidence()
        first = create_statistical_validation(_pending_finding())
        second = create_statistical_validation(first.finding)

        self.assertTrue(is_dataclass(first))
        self.assertTrue(is_dataclass(evidence))
        self.assertFalse(hasattr(first, "__dict__"))
        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        with self.assertRaises(FrozenInstanceError):
            first.note = "mutated"
        with self.assertRaises(FrozenInstanceError):
            evidence.left_sample_size = 2


def _pending_finding() -> ORBResearchFinding:
    """Build one eligible deterministic finding with its R3.1 request pending."""
    return request_statistical_validation(create_research_finding(_evaluation(4.0, 2.0)))


def _evidence() -> ORBStatisticalEvidence:
    """Build one future-test metadata record without performing a calculation."""
    return ORBStatisticalEvidence(
        test_identifier=ORBStatisticalTestIdentifier.WELCH_T_TEST,
        test_family=ORBStatisticalTestFamily.PARAMETRIC,
        left_sample_size=3,
        right_sample_size=2,
    )


def _evaluation(left: float, right: float):
    """Build one completed deterministic evaluation through the existing API."""
    return evaluate_behavior_hypothesis(
        _hypothesis(
            ORBHypothesisMetric.RANGE_SIZE_MEAN,
            ORBHypothesisRelation.GREATER_THAN,
        ),
        _range_atlas(left),
        _range_atlas(right),
    )


def _not_evaluable_evaluation():
    """Build existing unavailable deterministic evidence without replacements."""
    return evaluate_behavior_hypothesis(
        _hypothesis(
            ORBHypothesisMetric.RANGE_SIZE_MEAN,
            ORBHypothesisRelation.GREATER_THAN,
        ),
        build_behavior_atlas(()),
        build_behavior_atlas(()),
    )
