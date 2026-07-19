"""Private rule evaluation for canonical candle validation."""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from src.engines.data.models import Candle, Instrument, Timeframe
from src.engines.data.validation._models import ValidationCode

_MARKET_TIMEZONE_NAME = "Asia/Kolkata"


@dataclass(frozen=True, slots=True)
class _RuleFinding:
    """Private rule outcome, intentionally separate from public issue rendering."""

    code: ValidationCode
    field: str | None
    related_index: int | None
    rule_id: str


def evaluate_candle_rules(candle: Candle) -> tuple[_RuleFinding, ...]:
    """Evaluate semantic rules for one canonical candle without rendering issues."""
    findings: list[_RuleFinding] = []

    if not isinstance(candle.instrument, Instrument):
        findings.append(
            _RuleFinding(
                ValidationCode.UNSUPPORTED_INSTRUMENT,
                "instrument",
                None,
                "INSTRUMENT_SUPPORTED",
            )
        )
    if not isinstance(candle.timeframe, Timeframe):
        findings.append(
            _RuleFinding(
                ValidationCode.UNSUPPORTED_TIMEFRAME,
                "timeframe",
                None,
                "TIMEFRAME_SUPPORTED",
            )
        )

    if _is_naive(candle.timestamp):
        findings.append(
            _RuleFinding(
                ValidationCode.TIMESTAMP_NAIVE,
                "timestamp",
                None,
                "TIMESTAMP_TIMEZONE_AWARE",
            )
        )
    elif not _is_market_timestamp(candle.timestamp):
        findings.append(
            _RuleFinding(
                ValidationCode.TIMESTAMP_NOT_ASIA_KOLKATA,
                "timestamp",
                None,
                "TIMESTAMP_ASIA_KOLKATA",
            )
        )

    if candle.session_date != candle.timestamp.date():
        findings.append(
            _RuleFinding(
                ValidationCode.SESSION_DATE_MISMATCH,
                "session_date",
                None,
                "SESSION_DATE_MATCHES_TIMESTAMP",
            )
        )

    findings.extend(_evaluate_price_rules(candle))

    if candle.volume < 0:
        findings.append(
            _RuleFinding(
                ValidationCode.NEGATIVE_VOLUME,
                "volume",
                None,
                "VOLUME_NON_NEGATIVE",
            )
        )
    return tuple(findings)


def duplicate_timestamp_finding(*, related_index: int) -> _RuleFinding:
    """Return the private finding for a repeated canonical timestamp."""
    return _RuleFinding(
        ValidationCode.DUPLICATE_TIMESTAMP,
        "timestamp",
        related_index,
        "TIMESTAMP_UNIQUE",
    )


def timestamp_order_finding(*, related_index: int) -> _RuleFinding:
    """Return the private finding for a descending canonical timestamp."""
    return _RuleFinding(
        ValidationCode.TIMESTAMP_OUT_OF_ORDER,
        "timestamp",
        related_index,
        "TIMESTAMP_NONDECREASING",
    )


def _evaluate_price_rules(candle: Candle) -> tuple[_RuleFinding, ...]:
    """Evaluate negative-price and documented OHLC relationship rules."""
    findings: list[_RuleFinding] = []
    for field, value in (
        ("open", candle.open),
        ("high", candle.high),
        ("low", candle.low),
        ("close", candle.close),
    ):
        if value < 0:
            findings.append(
                _RuleFinding(
                    ValidationCode.NEGATIVE_PRICE,
                    field,
                    None,
                    "PRICE_NON_NEGATIVE",
                )
            )

    for code, field, rule_id, is_violated in (
        (
            ValidationCode.HIGH_BELOW_OPEN,
            "high",
            "OHLC_HIGH_GE_OPEN",
            candle.high < candle.open,
        ),
        (
            ValidationCode.HIGH_BELOW_CLOSE,
            "high",
            "OHLC_HIGH_GE_CLOSE",
            candle.high < candle.close,
        ),
        (
            ValidationCode.HIGH_BELOW_LOW,
            "high",
            "OHLC_HIGH_GE_LOW",
            candle.high < candle.low,
        ),
        (
            ValidationCode.LOW_ABOVE_OPEN,
            "low",
            "OHLC_LOW_LE_OPEN",
            candle.low > candle.open,
        ),
        (
            ValidationCode.LOW_ABOVE_CLOSE,
            "low",
            "OHLC_LOW_LE_CLOSE",
            candle.low > candle.close,
        ),
    ):
        if is_violated:
            findings.append(_RuleFinding(code, field, None, rule_id))
    return tuple(findings)


def _is_naive(timestamp: datetime) -> bool:
    """Return whether a timestamp lacks a usable UTC offset."""
    return timestamp.tzinfo is None or timestamp.utcoffset() is None


def _is_market_timestamp(timestamp: datetime) -> bool:
    """Return whether a timestamp uses the canonical market timezone identity."""
    return isinstance(timestamp.tzinfo, ZoneInfo) and timestamp.tzinfo.key == _MARKET_TIMEZONE_NAME
