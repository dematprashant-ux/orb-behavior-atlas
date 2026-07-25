"""Pure zero-safe risk-adjusted metrics over existing performance artifacts."""

from math import isfinite

from src.engines.performance.builders import build_risk_adjusted_metrics
from src.engines.performance.models import (
    DrawdownSummary,
    PerformanceMetrics,
    PerformanceMetricMode,
    RiskAdjustedMetrics,
    RiskAdjustedMetricMode,
)

__all__ = ["BasicRiskMetricsAnalyzer"]


class BasicRiskMetricsAnalyzer:
    """Calculate gross or net ratios from existing aggregate artifacts only."""

    def analyze(
        self,
        performance: PerformanceMetrics,
        drawdown: DrawdownSummary,
    ) -> RiskAdjustedMetrics:
        """Return identical zero-safe ratios from supplied aggregate artifacts.

        Args:
            performance: Existing immutable performance metrics.
            drawdown: Existing immutable absolute drawdown summary.

        Returns:
            Immutable ratios in the mode already selected by ``performance``,
            or ``None`` for both when maximum drawdown is zero.

        Raises:
            TypeError: If either input is not the required immutable model.
            ValueError: If native float division would produce a non-finite ratio.
        """
        if not isinstance(performance, PerformanceMetrics):
            raise TypeError("performance must be a PerformanceMetrics.")
        if not isinstance(drawdown, DrawdownSummary):
            raise TypeError("drawdown must be a DrawdownSummary.")
        mode = _risk_mode_for(performance.mode)
        if drawdown.maximum_drawdown == 0.0:
            return build_risk_adjusted_metrics(None, None, mode=mode)

        ratio = performance.net_profit / drawdown.maximum_drawdown
        if not isfinite(ratio):
            raise ValueError("risk-adjusted metrics must be finite.")
        return build_risk_adjusted_metrics(ratio, ratio, mode=mode)


def _risk_mode_for(performance_mode: PerformanceMetricMode) -> RiskAdjustedMetricMode:
    """Map the already-selected aggregate performance basis into result metadata."""
    if performance_mode is PerformanceMetricMode.GROSS:
        return RiskAdjustedMetricMode.GROSS
    return RiskAdjustedMetricMode.NET
