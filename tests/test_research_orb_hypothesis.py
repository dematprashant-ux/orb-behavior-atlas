"""Contract tests for deterministic explicit ORB behavior hypotheses."""

from dataclasses import FrozenInstanceError, is_dataclass
from math import inf, nan
from unittest import TestCase
from unittest.mock import patch

from src.engines.research import (
    ORBBehaviorHypothesis,
    ORBBehaviorHypothesisEvaluation,
    ORBBehaviorKind,
    ORBEscapeDirection,
    ORBHypothesisMetric,
    ORBHypothesisNotEvaluableReason,
    ORBHypothesisOutcome,
    ORBHypothesisRelation,
    build_behavior_atlas,
    compare_behavior_atlases,
    compute_behavior_descriptive_statistics,
    evaluate_behavior_hypothesis,
    group_by_escape_direction,
)
from tests.test_research_orb_descriptive_statistics import (
    _escape_record,
    _no_escape_record,
)


class ORBBehaviorHypothesisTests(TestCase):
    """Verify explicit conditions reuse canonical comparison facts only."""

    def test_greater_than_supported_with_threshold_and_differences(self) -> None:
        """Support a greater-than range mean when its threshold is exactly met."""
        evaluation = evaluate_behavior_hypothesis(
            _hypothesis(
                ORBHypothesisMetric.RANGE_SIZE_MEAN,
                ORBHypothesisRelation.GREATER_THAN,
                minimum_absolute_difference=2.0,
            ),
            _range_atlas(4.0),
            _range_atlas(2.0),
        )

        self.assertEqual(evaluation.outcome, ORBHypothesisOutcome.SUPPORTED)
        self.assertEqual(evaluation.left_value, 4.0)
        self.assertEqual(evaluation.right_value, 2.0)
        self.assertEqual(evaluation.signed_difference, 2.0)
        self.assertEqual(evaluation.absolute_difference, 2.0)

    def test_directional_relations_and_threshold_failures_are_deterministic(self) -> None:
        """Apply only each exact relation and the unrounded threshold boundary."""
        left = _range_atlas(2.0)
        right = _range_atlas(4.0)
        cases = (
            (ORBHypothesisRelation.GREATER_THAN, 0.0, False),
            (ORBHypothesisRelation.GREATER_THAN_OR_EQUAL, 2.0, False),
            (ORBHypothesisRelation.LESS_THAN, 2.0, True),
            (ORBHypothesisRelation.LESS_THAN_OR_EQUAL, 2.0, True),
            (ORBHypothesisRelation.LESS_THAN, 3.0, False),
        )

        for relation, threshold, expected_supported in cases:
            with self.subTest(relation=relation, threshold=threshold):
                evaluation = evaluate_behavior_hypothesis(
                    _hypothesis(
                        ORBHypothesisMetric.RANGE_SIZE_MEAN,
                        relation,
                        minimum_absolute_difference=threshold,
                    ),
                    left,
                    right,
                )
                expected = (
                    ORBHypothesisOutcome.SUPPORTED
                    if expected_supported
                    else ORBHypothesisOutcome.NOT_SUPPORTED
                )
                self.assertEqual(evaluation.outcome, expected)

    def test_equality_supports_exact_values_and_rejects_positive_threshold(self) -> None:
        """Keep equality exact and prohibit ambiguous positive tolerance bounds."""
        supported = evaluate_behavior_hypothesis(
            _hypothesis(
                ORBHypothesisMetric.RANGE_SIZE_MEDIAN,
                ORBHypothesisRelation.EQUAL,
            ),
            _range_atlas(4.0),
            _range_atlas(4.0),
        )
        not_supported = evaluate_behavior_hypothesis(
            _hypothesis(
                ORBHypothesisMetric.RANGE_SIZE_MEDIAN,
                ORBHypothesisRelation.EQUAL,
            ),
            _range_atlas(4.0),
            _range_atlas(2.0),
        )

        self.assertEqual(supported.outcome, ORBHypothesisOutcome.SUPPORTED)
        self.assertEqual(not_supported.outcome, ORBHypothesisOutcome.NOT_SUPPORTED)
        with self.assertRaisesRegex(ValueError, "EQUAL"):
            _hypothesis(
                ORBHypothesisMetric.RANGE_SIZE_MEAN,
                ORBHypothesisRelation.EQUAL,
                minimum_absolute_difference=0.1,
            )

    def test_non_strict_relations_support_exact_boundaries(self) -> None:
        """Support equal observations only through their non-strict relations."""
        left = _range_atlas(4.0)
        right = _range_atlas(4.0)
        for relation in (
            ORBHypothesisRelation.GREATER_THAN_OR_EQUAL,
            ORBHypothesisRelation.LESS_THAN_OR_EQUAL,
        ):
            with self.subTest(relation=relation):
                evaluation = evaluate_behavior_hypothesis(
                    _hypothesis(
                        ORBHypothesisMetric.RANGE_SIZE_MEAN,
                        relation,
                    ),
                    left,
                    right,
                )
                self.assertEqual(evaluation.outcome, ORBHypothesisOutcome.SUPPORTED)

    def test_less_than_not_supported_when_left_value_is_higher(self) -> None:
        """Reject a strict less-than condition when the observed direction reverses."""
        evaluation = evaluate_behavior_hypothesis(
            _hypothesis(
                ORBHypothesisMetric.RANGE_SIZE_MEAN,
                ORBHypothesisRelation.LESS_THAN,
            ),
            _range_atlas(4.0),
            _range_atlas(2.0),
        )

        self.assertEqual(evaluation.outcome, ORBHypothesisOutcome.NOT_SUPPORTED)

    def test_threshold_validation_rejects_intrinsically_invalid_values(self) -> None:
        """Require finite non-boolean non-negative explicit threshold values."""
        for threshold in (-1.0, nan, inf, -inf, True):
            with self.subTest(threshold=threshold):
                with self.assertRaises(ValueError):
                    _hypothesis(
                        ORBHypothesisMetric.RANGE_SIZE_MEAN,
                        ORBHypothesisRelation.GREATER_THAN,
                        minimum_absolute_difference=threshold,
                    )

    def test_numeric_mean_and_median_metrics_cover_range_mfe_and_mae(self) -> None:
        """Resolve only existing numeric summaries without recalculating them."""
        left = build_behavior_atlas(
            (
                _escape_record(
                    range_size=6.0,
                    direction=ORBEscapeDirection.UPWARD,
                    returned=True,
                    mfe=4.0,
                    mae=3.0,
                ),
            )
        )
        right = build_behavior_atlas(
            (
                _escape_record(
                    range_size=2.0,
                    direction=ORBEscapeDirection.DOWNWARD,
                    returned=False,
                    mfe=1.0,
                    mae=1.0,
                ),
            )
        )
        metrics = (
            ORBHypothesisMetric.RANGE_SIZE_MEAN,
            ORBHypothesisMetric.RANGE_SIZE_MEDIAN,
            ORBHypothesisMetric.MAXIMUM_FAVORABLE_EXCURSION_MEAN,
            ORBHypothesisMetric.MAXIMUM_FAVORABLE_EXCURSION_MEDIAN,
            ORBHypothesisMetric.MAXIMUM_ADVERSE_EXCURSION_MEAN,
            ORBHypothesisMetric.MAXIMUM_ADVERSE_EXCURSION_MEDIAN,
        )

        for metric in metrics:
            with self.subTest(metric=metric):
                evaluation = evaluate_behavior_hypothesis(
                    _hypothesis(metric, ORBHypothesisRelation.GREATER_THAN),
                    left,
                    right,
                )
                self.assertEqual(evaluation.outcome, ORBHypothesisOutcome.SUPPORTED)

    def test_categorical_proportion_metrics_use_explicit_existing_categories(self) -> None:
        """Resolve behavior, direction, and return proportions from each side."""
        left = _categorical_atlas(
            (
                (ORBEscapeDirection.UPWARD, True, 2.0),
                (ORBEscapeDirection.DOWNWARD, False, 4.0),
            )
        )
        right = _categorical_atlas(
            (
                (ORBEscapeDirection.UPWARD, True, 6.0),
                (ORBEscapeDirection.UPWARD, True, 8.0),
            )
        )
        cases = (
            (
                _hypothesis(
                    ORBHypothesisMetric.BEHAVIOR_PROPORTION,
                    ORBHypothesisRelation.LESS_THAN,
                    category=ORBBehaviorKind.ESCAPE_WITH_RETURN,
                ),
                ORBHypothesisOutcome.SUPPORTED,
            ),
            (
                _hypothesis(
                    ORBHypothesisMetric.ESCAPE_DIRECTION_PROPORTION,
                    ORBHypothesisRelation.LESS_THAN,
                    category=ORBEscapeDirection.UPWARD,
                ),
                ORBHypothesisOutcome.SUPPORTED,
            ),
            (
                _hypothesis(
                    ORBHypothesisMetric.RETURN_TO_RANGE_PROPORTION,
                    ORBHypothesisRelation.LESS_THAN,
                    category=True,
                ),
                ORBHypothesisOutcome.SUPPORTED,
            ),
        )

        for hypothesis, expected in cases:
            with self.subTest(metric=hypothesis.metric):
                evaluation = evaluate_behavior_hypothesis(hypothesis, left, right)
                self.assertEqual(evaluation.outcome, expected)

    def test_category_requirements_reject_missing_or_wrong_category_types(self) -> None:
        """Keep every categorical metric bound to its existing category type."""
        with self.assertRaises(TypeError):
            _hypothesis(
                ORBHypothesisMetric.BEHAVIOR_PROPORTION,
                ORBHypothesisRelation.EQUAL,
            )
        with self.assertRaises(TypeError):
            _hypothesis(
                ORBHypothesisMetric.ESCAPE_DIRECTION_PROPORTION,
                ORBHypothesisRelation.EQUAL,
                category=ORBBehaviorKind.NO_ESCAPE,
            )
        with self.assertRaises(TypeError):
            _hypothesis(
                ORBHypothesisMetric.RETURN_TO_RANGE_PROPORTION,
                ORBHypothesisRelation.EQUAL,
                category=1,
            )
        with self.assertRaises(ValueError):
            _hypothesis(
                ORBHypothesisMetric.RANGE_SIZE_MEAN,
                ORBHypothesisRelation.EQUAL,
                category=ORBBehaviorKind.NO_ESCAPE,
            )

    def test_empty_and_missing_observations_return_stable_not_evaluable_reasons(self) -> None:
        """Preserve unavailable canonical values rather than replacing them."""
        populated = _range_atlas(2.0)
        empty = build_behavior_atlas(())
        range_hypothesis = _hypothesis(
            ORBHypothesisMetric.RANGE_SIZE_MEAN,
            ORBHypothesisRelation.GREATER_THAN,
        )
        both_empty = evaluate_behavior_hypothesis(range_hypothesis, empty, empty)
        left_empty = evaluate_behavior_hypothesis(range_hypothesis, empty, populated)
        right_empty = evaluate_behavior_hypothesis(range_hypothesis, populated, empty)
        escaped = build_behavior_atlas(
            (
                _escape_record(
                    range_size=4.0,
                    direction=ORBEscapeDirection.UPWARD,
                    returned=True,
                    mfe=2.0,
                    mae=1.0,
                ),
            )
        )
        left_missing_mfe = evaluate_behavior_hypothesis(
            _hypothesis(
                ORBHypothesisMetric.MAXIMUM_FAVORABLE_EXCURSION_MEAN,
                ORBHypothesisRelation.GREATER_THAN,
            ),
            populated,
            escaped,
        )
        right_missing_mfe = evaluate_behavior_hypothesis(
            _hypothesis(
                ORBHypothesisMetric.MAXIMUM_FAVORABLE_EXCURSION_MEAN,
                ORBHypothesisRelation.GREATER_THAN,
            ),
            escaped,
            populated,
        )
        missing_mfe = evaluate_behavior_hypothesis(
            _hypothesis(
                ORBHypothesisMetric.MAXIMUM_FAVORABLE_EXCURSION_MEAN,
                ORBHypothesisRelation.GREATER_THAN,
            ),
            populated,
            _range_atlas(4.0),
        )
        missing_category = evaluate_behavior_hypothesis(
            _hypothesis(
                ORBHypothesisMetric.BEHAVIOR_PROPORTION,
                ORBHypothesisRelation.EQUAL,
                category=ORBBehaviorKind.ESCAPE_WITH_RETURN,
            ),
            populated,
            _range_atlas(4.0),
        )

        self.assertEqual(
            both_empty.not_evaluable_reason,
            ORBHypothesisNotEvaluableReason.BOTH_VALUES_UNAVAILABLE,
        )
        self.assertEqual(
            left_empty.not_evaluable_reason,
            ORBHypothesisNotEvaluableReason.LEFT_VALUE_UNAVAILABLE,
        )
        self.assertEqual(
            right_empty.not_evaluable_reason,
            ORBHypothesisNotEvaluableReason.RIGHT_VALUE_UNAVAILABLE,
        )
        self.assertEqual(
            left_missing_mfe.not_evaluable_reason,
            ORBHypothesisNotEvaluableReason.LEFT_VALUE_UNAVAILABLE,
        )
        self.assertEqual(
            right_missing_mfe.not_evaluable_reason,
            ORBHypothesisNotEvaluableReason.RIGHT_VALUE_UNAVAILABLE,
        )
        self.assertEqual(
            missing_mfe.not_evaluable_reason,
            ORBHypothesisNotEvaluableReason.BOTH_VALUES_UNAVAILABLE,
        )
        self.assertEqual(
            missing_category.not_evaluable_reason,
            ORBHypothesisNotEvaluableReason.BOTH_VALUES_UNAVAILABLE,
        )
        self.assertIsNone(right_empty.signed_difference)
        self.assertIsNone(right_empty.absolute_difference)

    def test_filtered_atlases_reuse_one_canonical_comparison_without_mutation(self) -> None:
        """Receive caller-selected subsets and compose comparison exactly once."""
        upward = _escape_record(
            range_size=4.0,
            direction=ORBEscapeDirection.UPWARD,
            returned=True,
            mfe=2.0,
            mae=1.0,
        )
        downward = _escape_record(
            range_size=2.0,
            direction=ORBEscapeDirection.DOWNWARD,
            returned=False,
            mfe=1.0,
            mae=2.0,
        )
        atlas = build_behavior_atlas((upward, downward))
        left = group_by_escape_direction(atlas).groups[ORBEscapeDirection.UPWARD]
        right = atlas.filter(escape_direction=ORBEscapeDirection.DOWNWARD)

        with patch(
            "src.engines.research.orb.hypothesis.compare_behavior_atlases",
            wraps=compare_behavior_atlases,
        ) as comparison_function:
            evaluation = evaluate_behavior_hypothesis(
                _hypothesis(
                    ORBHypothesisMetric.RANGE_SIZE_MEAN,
                    ORBHypothesisRelation.GREATER_THAN,
                ),
                left,
                right,
            )

        self.assertEqual(comparison_function.call_count, 1)
        self.assertEqual(comparison_function.call_args.args, (left, right))
        self.assertEqual(evaluation.outcome, ORBHypothesisOutcome.SUPPORTED)
        self.assertEqual(tuple(atlas), (upward, downward))

    def test_comparison_and_descriptive_statistics_are_reused_without_copying(self) -> None:
        """Retain the exact canonical comparison produced for the evaluation."""
        left = _range_atlas(4.0)
        right = _range_atlas(2.0)
        hypothesis = _hypothesis(
            ORBHypothesisMetric.RANGE_SIZE_MEAN,
            ORBHypothesisRelation.GREATER_THAN,
        )
        with patch(
            "src.engines.research.orb.comparison."
            "compute_behavior_descriptive_statistics",
            wraps=compute_behavior_descriptive_statistics,
        ) as descriptive:
            evaluation = evaluate_behavior_hypothesis(hypothesis, left, right)

        self.assertEqual(descriptive.call_count, 2)
        self.assertEqual(descriptive.call_args_list[0].args, (left,))
        self.assertEqual(descriptive.call_args_list[1].args, (right,))
        self.assertIs(evaluation.hypothesis, hypothesis)
        self.assertIsNotNone(evaluation.comparison)

    def test_evaluation_is_deterministic_immutable_and_publicly_exported(self) -> None:
        """Expose frozen public values with deterministic equality and repr."""
        hypothesis = _hypothesis(
            ORBHypothesisMetric.RANGE_SIZE_MEAN,
            ORBHypothesisRelation.GREATER_THAN_OR_EQUAL,
        )
        first = evaluate_behavior_hypothesis(
            hypothesis,
            _range_atlas(4.0),
            _range_atlas(2.0),
        )
        second = evaluate_behavior_hypothesis(
            hypothesis,
            _range_atlas(4.0),
            _range_atlas(2.0),
        )

        self.assertIsInstance(first, ORBBehaviorHypothesisEvaluation)
        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.outcome = ORBHypothesisOutcome.NOT_SUPPORTED


def _hypothesis(
    metric: ORBHypothesisMetric,
    relation: ORBHypothesisRelation,
    *,
    category: ORBBehaviorKind | ORBEscapeDirection | bool | None = None,
    minimum_absolute_difference: float = 0.0,
) -> ORBBehaviorHypothesis:
    """Build one explicit immutable test hypothesis using public construction."""
    return ORBBehaviorHypothesis(
        metric=metric,
        relation=relation,
        category=category,
        minimum_absolute_difference=minimum_absolute_difference,
    )


def _range_atlas(range_size: float):
    """Build one deterministic completed no-escape atlas with a known range."""
    return build_behavior_atlas((_no_escape_record(range_size=range_size),))


def _categorical_atlas(
    facts: tuple[tuple[ORBEscapeDirection, bool, float], ...],
):
    """Build deterministic escaped records for categorical proportion tests."""
    return build_behavior_atlas(
        tuple(
            _escape_record(
                range_size=range_size,
                direction=direction,
                returned=returned,
                mfe=range_size,
                mae=range_size,
            )
            for direction, returned, range_size in facts
        )
    )
