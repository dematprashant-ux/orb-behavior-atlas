"""Single-candle canonical validation orchestration."""

from src.engines.data.models import Candle
from src.engines.data.validation._issues import build_issue
from src.engines.data.validation._models import CandleValidationResult
from src.engines.data.validation._rules import evaluate_candle_rules


def validate_candle(candle: Candle) -> CandleValidationResult:
    """Return all semantic validation issues for one canonical candle."""
    if not isinstance(candle, Candle):
        raise TypeError("candle must be a Candle")
    return CandleValidationResult(
        candle=candle,
        issues=tuple(build_issue(finding) for finding in evaluate_candle_rules(candle)),
    )
