"""Contract tests for immutable reports over completed optimization selections."""

from dataclasses import FrozenInstanceError
from unittest import TestCase
from unittest.mock import patch

from src.engines.backtesting import (
    ConstraintDiagnostics,
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveSelection,
    OptimizationProgress,
    OptimizationResultReport,
    OptimizationRun,
    OptimizationSearchRun,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    StandardObjectiveRanker,
    TopRankedSelectionPolicy,
)


class OptimizationResultReportTests(TestCase):
    """Verify immutable identity-preserving reports without stage execution."""

    def test_factory_retains_exact_compatible_run_and_selection_identities(
        self,
    ) -> None:
        run = _run()

        report = OptimizationResultReport.from_run_and_selection(run, run.selection)

        self.assertIs(report.run, run)
        self.assertIs(report.selection, run.selection)
        self.assertEqual(
            report,
            OptimizationResultReport.from_run_and_selection(run, run.selection),
        )
        self.assertEqual(
            repr(report),
            repr(OptimizationResultReport.from_run_and_selection(run, run.selection)),
        )
        with self.assertRaises(FrozenInstanceError):
            report.run = run  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            report.selection = run.selection  # type: ignore[misc]

    def test_factory_rejects_invalid_types_and_unrelated_selection_immediately(
        self,
    ) -> None:
        run = _run()
        other_run = _run()

        for value in (None, (), {}, "run"):
            with self.subTest(run=value), self.assertRaisesRegex(TypeError, "run"):
                OptimizationResultReport.from_run_and_selection(
                    value, run.selection
                )  # type: ignore[arg-type]
        for value in (None, (), run.ranking, object()):
            with self.subTest(selection=value), self.assertRaisesRegex(
                TypeError,
                "selection",
            ):
                OptimizationResultReport.from_run_and_selection(
                    run, value
                )  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "exact ranking"):
            OptimizationResultReport.from_run_and_selection(
                run,
                other_run.selection,
            )

    def test_factory_does_not_execute_ranking_or_selection(self) -> None:
        run = _run()

        with patch.object(
            StandardObjectiveRanker,
            "rank",
            side_effect=AssertionError("ranking must not execute"),
        ), patch.object(
            TopRankedSelectionPolicy,
            "select",
            side_effect=AssertionError("selection must not execute"),
        ):
            report = OptimizationResultReport.from_run_and_selection(
                run,
                run.selection,
            )

        self.assertIs(report.run, run)
        self.assertIs(report.selection, run.selection)

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import OptimizationResultReport as PackageReport
        from src.engines.backtesting.summary import (
            OptimizationResultReport as ModuleReport,
        )

        self.assertIs(PackageReport, OptimizationResultReport)
        self.assertIs(ModuleReport, OptimizationResultReport)


def _run() -> OptimizationRun:
    """Return one completed run with its only canonical empty selection."""
    ranking = ObjectiveRanking(ObjectiveDirection.MAXIMIZE)
    search_run = OptimizationSearchRun(
        OptimizationStrategyMetadata("test"),
        (),
        OptimizationProgress(0, 0),
        OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
        ConstraintDiagnostics(),
    )
    return OptimizationRun(search_run, (), ranking, ObjectiveSelection(ranking))
