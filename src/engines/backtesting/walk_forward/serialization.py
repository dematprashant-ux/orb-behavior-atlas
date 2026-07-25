"""Deterministic plain-data serialization for walk-forward reports."""

from src.engines.backtesting.walk_forward.reporting import WalkForwardReport

__all__ = ["DictionaryWalkForwardReportSerializer"]


class DictionaryWalkForwardReportSerializer:
    """Serialize existing report facts into JSON-safe ordered plain data."""

    def serialize(self, report: WalkForwardReport) -> dict[str, object]:
        """Return stable plain data without calculations, rendering, or I/O."""
        if not isinstance(report, WalkForwardReport):
            raise TypeError("report must be a WalkForwardReport.")
        summary = report.summary
        return {
            "report_type": report.report_type.value,
            "summary": {
                "total_windows": summary.total_windows,
                "completed_iterations": summary.completed_iterations,
                "earliest_training_start": _serialize_datetime(
                    summary.earliest_training_start
                ),
                "latest_validation_end": _serialize_datetime(
                    summary.latest_validation_end
                ),
            },
            "iterations": [
                {
                    "window_index": iteration.source_window.index,
                    "training_range": _serialize_range(
                        iteration.source_window.training_range.start,
                        iteration.source_window.training_range.end,
                    ),
                    "validation_range": _serialize_range(
                        iteration.source_window.validation_range.start,
                        iteration.source_window.validation_range.end,
                    ),
                    "training_observation_count": len(iteration.training.observations),
                    "validation_observation_count": len(
                        iteration.validation.observations
                    ),
                    "selection_id": iteration.selection.selection_id,
                }
                for iteration in report.run.iterations
            ],
        }


def _serialize_range(start: object, end: object) -> dict[str, object]:
    """Return existing range boundaries as JSON-safe ISO-8601 strings."""
    return {
        "start": _serialize_datetime(start),
        "end": _serialize_datetime(end),
    }


def _serialize_datetime(value: object) -> str | None:
    """Serialize an existing aware datetime without adding any runtime timestamp."""
    if value is None:
        return None
    isoformat = getattr(value, "isoformat", None)
    if not callable(isoformat):
        raise TypeError("report timestamps must support isoformat().")
    return isoformat()
