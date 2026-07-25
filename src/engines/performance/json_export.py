"""Deterministic compact JSON export for plain backtest-report data."""

import json
from collections.abc import Mapping
from dataclasses import dataclass

__all__ = ["StandardJsonReportExporter"]


@dataclass(frozen=True, slots=True)
class StandardJsonReportExporter:
    """Export plain report data to compact stable-key JSON without side effects."""

    def export(self, serialized_report: Mapping[str, object]) -> str:
        """Return deterministic UTF-8-compatible compact JSON.

        Existing plain values are encoded unchanged. Key ordering is stable,
        collection ordering is preserved, and non-finite numeric values are
        rejected because they are not valid standard JSON.

        Args:
            serialized_report: Plain data produced by ``DictionaryReportSerializer``.

        Returns:
            Compact JSON with lexicographically stable object keys.

        Raises:
            TypeError: If ``serialized_report`` is not a mapping or has data that
                cannot be encoded as JSON.
            ValueError: If a numeric value is non-finite.
        """
        if not isinstance(serialized_report, Mapping):
            raise TypeError("serialized_report must be a Mapping.")
        return json.dumps(
            dict(serialized_report),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
