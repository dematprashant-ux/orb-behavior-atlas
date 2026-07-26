"""Integration tests for the BANKNIFTY CSV-to-ORB research pipeline."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zoneinfo import ZoneInfo

from src.engines.data import DataEngineOrchestrator, ExecutionStatus
from src.engines.research import (
    BankNiftyCsvOrbResearchPipeline,
    ORBBehaviorKind,
)

_HEADER = "timestamp,open,high,low,close,volume\n"


class BankNiftyCsvOrbResearchPipelineTests(unittest.TestCase):
    """Verify CSV ingestion is composed into immutable completed ORB records."""

    def test_csv_to_behavior_records_composes_the_canonical_pipeline(self) -> None:
        """Two valid sessions produce ordered records through existing components."""
        result = self._pipeline().run(
            self._csv_path(_valid_csv()),
            start_date=date(2026, 7, 17),
            end_date=date(2026, 7, 20),
        )

        self.assertEqual(result.data_execution.status, ExecutionStatus.COMPLETED)
        self.assertEqual(len(result.data_execution.sessions), 2)
        self.assertEqual(len(result.behavior_atlas), 2)
        self.assertEqual(
            [record.behavior.kind for record in result.behavior_atlas],
            [
                ORBBehaviorKind.NO_ESCAPE,
                ORBBehaviorKind.ESCAPE_WITH_RETURN,
            ],
        )

    def test_repeated_execution_is_deterministic(self) -> None:
        """The same immutable CSV facts produce value-equal pipeline outputs."""
        path = self._csv_path(_valid_csv())
        pipeline = self._pipeline()

        first = pipeline.run(
            path,
            start_date=date(2026, 7, 17),
            end_date=date(2026, 7, 20),
        )
        second = pipeline.run(
            path,
            start_date=date(2026, 7, 17),
            end_date=date(2026, 7, 20),
        )

        self.assertEqual(first, second)

    def test_rejected_data_execution_produces_no_behavior_records(self) -> None:
        """Invalid candles remain rejected by Data Engine validation before research."""
        result = self._pipeline().run(
            self._csv_path(
                _HEADER + "2026-07-17T09:15:00,100,99,98,100.5,10\n"
            ),
            start_date=date(2026, 7, 17),
            end_date=date(2026, 7, 17),
        )

        self.assertEqual(result.data_execution.status, ExecutionStatus.REJECTED)
        self.assertEqual(result.data_execution.sessions, ())
        self.assertEqual(len(result.behavior_atlas), 0)

    def test_session_without_a_complete_opening_window_is_omitted(self) -> None:
        """Existing ORB extraction rejection does not create a partial record."""
        result = self._pipeline().run(
            self._csv_path(
                _HEADER
                + "2026-07-17T09:15:00,100,101,99,100.5,10\n"
                + "2026-07-17T09:20:00,100.5,101.5,100,101,11\n"
            ),
            start_date=date(2026, 7, 17),
            end_date=date(2026, 7, 17),
        )

        self.assertEqual(result.data_execution.status, ExecutionStatus.COMPLETED)
        self.assertEqual(len(result.data_execution.sessions), 1)
        self.assertEqual(len(result.behavior_atlas), 0)

    def _pipeline(self) -> BankNiftyCsvOrbResearchPipeline:
        """Construct the pipeline with the canonical injected Data Engine service."""
        return BankNiftyCsvOrbResearchPipeline(
            data_engine=DataEngineOrchestrator(),
            source_timezone=ZoneInfo("Asia/Kolkata"),
        )

    def _csv_path(self, content: str) -> Path:
        """Write one deterministic source fixture outside the repository tree."""
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "banknifty.csv"
        path.write_text(content, encoding="utf-8")
        return path


def _valid_csv() -> str:
    """Return two valid sessions with no escape then an upward return."""
    return (
        _HEADER
        + "2026-07-17T09:15:00,100,102,99,101,10\n"
        + "2026-07-17T09:20:00,101,103,100,102,11\n"
        + "2026-07-17T09:25:00,102,102.5,100.5,101,12\n"
        + "2026-07-17T09:30:00,101,103,100,102,13\n"
        + "2026-07-20T09:15:00,200,202,199,201,10\n"
        + "2026-07-20T09:20:00,201,203,200,202,11\n"
        + "2026-07-20T09:25:00,202,202.5,201,201.5,12\n"
        + "2026-07-20T09:30:00,202,204,202,203,13\n"
        + "2026-07-20T09:35:00,203,204,201,202,14\n"
    )


if __name__ == "__main__":
    unittest.main()
