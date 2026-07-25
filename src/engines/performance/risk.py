"""Pure zero-safe risk-adjusted metrics over existing performance artifacts."""

from math import isfinite

from src.engines.performance.builders import build_risk_adjusted_metrics
from src.engines.performance.models import (
    DrawdownSummary,
    PerformanceMetrics,
    RiskAdjustedMetrics,
)

__all__ = ["BasicRiskMetricsAnalyzer"]


class BasicRiskMetricsAnalyzer:
    """Calculate absolute return-over-drawdown values without portfolio analysis."""

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
            Immutable recovery-factor and return-over-drawdown values, or
            ``None`` for both when maximum drawdown is zero.

        Raises:
            TypeError: If either input is not the required immutable model.
            ValueError: If native float division would produce a non-finite ratio.
        """
        if not isinstance(performance, PerformanceMetrics):
            raise TypeError("performance must be a PerformanceMetrics.")
        if not isinstance(drawdown, DrawdownSummary):
            raise TypeError("drawdown must be a DrawdownSummary.")
        if drawdown.maximum_drawdown == 0.0:
            return build_risk_adjusted_metrics(None, None)

        ratio = performance.net_profit / drawdown.maximum_drawdown
        if not isfinite(ratio):
            raise ValueError("risk-adjusted metrics must be finite.")
        return build_risk_adjusted_metrics(ratio, ratio)
