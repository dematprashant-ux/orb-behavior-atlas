"""Deterministic local CSV adapter for BANKNIFTY five-minute history."""

import csv
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engines.data.exceptions import DataSourceError
from src.engines.data.models import Candle, Instrument, Timeframe
from src.engines.data.providers._base import BaseProviderAdapter
from src.engines.data.providers._config import ProviderConfig

_CANONICAL_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")


class BankNiftyM5CsvProvider(BaseProviderAdapter):
    """Load ordered UTF-8 BANKNIFTY M5 CSV records through canonical normalization."""

    def __init__(self, path: Path, *, source_timezone: ZoneInfo) -> None:
        """Configure one local CSV source and its declared timestamp timezone."""
        if not isinstance(path, Path):
            raise TypeError("path must be a Path")
        if not path.name:
            raise ValueError("path must identify a file")

        super().__init__(
            ProviderConfig(
                provider_name="banknifty-m5-csv",
                source_timezone=source_timezone,
                instrument_codes=((Instrument.BANKNIFTY, "BANKNIFTY"),),
                timeframe_codes=((Timeframe.M5, "M5"),),
            )
        )
        self._path = path

    def fetch(
        self,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
        start_date: date,
        end_date: date,
    ) -> Sequence[Candle]:
        """Return normalized candles whose canonical session dates are in range."""
        candles = super().fetch(
            instrument=instrument,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )
        return tuple(
            candle
            for candle in candles
            if start_date <= candle.session_date <= end_date
        )

    def _fetch_payloads(
        self,
        *,
        provider_instrument: str,
        provider_timeframe: str,
        start_date: date,
        end_date: date,
    ) -> Iterable[object]:
        """Read source-order CSV rows without applying candle validation rules."""
        del provider_instrument, provider_timeframe, start_date, end_date

        try:
            with self._path.open("r", encoding="utf-8", newline="") as source_file:
                rows = csv.reader(source_file, strict=True)
                header = next(rows, None)
                if header is None:
                    raise DataSourceError("CSV source is empty.")
                _validate_header(header)

                payloads = tuple(
                    _row_to_payload(header, row, row_number=index)
                    for index, row in enumerate(rows, start=2)
                )
        except DataSourceError:
            raise
        except UnicodeDecodeError as error:
            raise DataSourceError("CSV source is not valid UTF-8.") from error
        except csv.Error as error:
            raise DataSourceError("CSV source has malformed structure.") from error
        except OSError as error:
            raise DataSourceError("CSV source could not be read.") from error

        if not payloads:
            raise DataSourceError("CSV source contains no records.")
        return payloads

    def _parse_payload(self, payload: object) -> Mapping[str, object]:
        """Map one structurally valid CSV row into the canonical mapping contract."""
        if not isinstance(payload, Mapping):
            raise TypeError("CSV payload must be a mapping")

        timestamp = payload["timestamp"]
        if not isinstance(timestamp, str):
            raise TypeError("CSV timestamp must be a string")
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp)
        except ValueError as error:
            raise DataSourceError("CSV timestamp is invalid.") from error

        return {
            "timestamp": parsed_timestamp,
            "open": payload["open"],
            "high": payload["high"],
            "low": payload["low"],
            "close": payload["close"],
            "volume": payload["volume"],
        }


def _validate_header(header: list[str]) -> None:
    """Reject CSV schemas that cannot produce the canonical mapping exactly."""
    if len(set(header)) != len(header):
        raise DataSourceError("CSV source contains duplicate column names.")
    if tuple(header) != _CANONICAL_COLUMNS:
        missing = set(_CANONICAL_COLUMNS).difference(header)
        if missing:
            raise DataSourceError("CSV source is missing required columns.")
        raise DataSourceError("CSV source contains unsupported columns.")


def _row_to_payload(
    header: list[str],
    row: list[str],
    *,
    row_number: int,
) -> dict[str, str]:
    """Return a complete source row as a canonical-keyed mapping."""
    if not row or all(not value.strip() for value in row):
        raise DataSourceError(
            f"CSV source contains a blank record at row {row_number}."
        )
    if len(row) != len(header) or any(not value.strip() for value in row):
        raise DataSourceError(
            f"CSV source contains an incomplete record at row {row_number}."
        )
    return dict(zip(header, row, strict=True))


__all__ = ["BankNiftyM5CsvProvider"]
