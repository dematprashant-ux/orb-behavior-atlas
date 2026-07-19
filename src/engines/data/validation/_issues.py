"""Private construction of deterministic public validation issues."""

from src.engines.data.validation._models import ValidationIssue, ValidationSeverity
from src.engines.data.validation._rules import _RuleFinding

_MESSAGES = {
    "UNSUPPORTED_INSTRUMENT": "Candle instrument is not supported.",
    "UNSUPPORTED_TIMEFRAME": "Candle timeframe is not supported.",
    "TIMESTAMP_NAIVE": "Candle timestamp must be timezone-aware.",
    "TIMESTAMP_NOT_ASIA_KOLKATA": "Candle timestamp must use Asia/Kolkata.",
    "SESSION_DATE_MISMATCH": "Candle session date must match its timestamp date.",
    "NEGATIVE_PRICE": "Candle price must be non-negative.",
    "HIGH_BELOW_OPEN": "Candle high must be greater than or equal to open.",
    "HIGH_BELOW_CLOSE": "Candle high must be greater than or equal to close.",
    "HIGH_BELOW_LOW": "Candle high must be greater than or equal to low.",
    "LOW_ABOVE_OPEN": "Candle low must be less than or equal to open.",
    "LOW_ABOVE_CLOSE": "Candle low must be less than or equal to close.",
    "NEGATIVE_VOLUME": "Candle volume must be non-negative.",
    "DUPLICATE_TIMESTAMP": "Candle timestamp duplicates an earlier canonical candle.",
    "TIMESTAMP_OUT_OF_ORDER": "Candle timestamp is earlier than the prior canonical candle.",
}


def build_issue(finding: _RuleFinding) -> ValidationIssue:
    """Render a private finding as a deterministic public error issue."""
    return ValidationIssue(
        code=finding.code,
        severity=ValidationSeverity.ERROR,
        message=_MESSAGES[finding.code.value],
        field=finding.field,
        related_index=finding.related_index,
        rule_id=finding.rule_id,
    )
