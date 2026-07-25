"""Deterministic in-memory serialization of immutable backtest reports."""

from src.engines.performance.models import (
    BacktestReport,
    EquityPoint,
    TradePnL,
)

__all__ = ["DictionaryReportSerializer"]


class DictionaryReportSerializer:
    """Serialize existing report artifacts into nested plain dictionary data."""

    def serialize(self, report: BacktestReport) -> dict[str, object]:
        """Return a deterministic ordered plain-data representation of ``report``.

        The returned dictionaries and lists contain only existing field values.
        No metric is recalculated, rounded, rendered, written, or persisted.

        Args:
            report: Existing immutable report containing analytics artifacts.

        Returns:
            Nested plain data preserving report collection order and ``None``.

        Raises:
            TypeError: If ``report`` is not a ``BacktestReport``.
        """
        if not isinstance(report, BacktestReport):
            raise TypeError("report must be a BacktestReport.")

        performance = report.performance_metrics
        curve = report.equity_curve
        drawdown = report.drawdown_summary
        risk = report.risk_adjusted_metrics
        return {
            "report_mode": report.mode.value.lower(),
            "performance_metrics": {
                "total_trades": performance.total_trades,
                "winning_trades": performance.winning_trades,
                "losing_trades": performance.losing_trades,
                "flat_trades": performance.flat_trades,
                "gross_profit": performance.gross_profit,
                "gross_loss": performance.gross_loss,
                "net_profit": performance.net_profit,
                "win_rate": performance.win_rate,
                "loss_rate": performance.loss_rate,
                "flat_rate": performance.flat_rate,
                "average_trade_pnl": performance.average_trade_pnl,
                "average_winning_trade": performance.average_winning_trade,
                "average_losing_trade": performance.average_losing_trade,
                "profit_factor": performance.profit_factor,
                "expectancy": performance.expectancy,
            },
            "equity_curve": {
                "points": [
                    _serialize_equity_point(point) for point in curve.equity_points
                ],
                "final_equity": curve.final_equity,
            },
            "drawdown_summary": {
                "points": [
                    {
                        "source_equity_point": _serialize_equity_point(
                            point.source_equity_point
                        ),
                        "running_peak": point.running_peak,
                        "drawdown": point.drawdown,
                    }
                    for point in drawdown.drawdown_points
                ],
                "maximum_drawdown": drawdown.maximum_drawdown,
            },
            "risk_adjusted_metrics": {
                "recovery_factor": risk.recovery_factor,
                "return_over_drawdown": risk.return_over_drawdown,
            },
        }


def _serialize_equity_point(point: EquityPoint) -> dict[str, object]:
    """Return one existing cumulative-equity point as nested plain data."""
    return {
        "source_trade_pnl": _serialize_trade_pnl(point.source_trade_pnl),
        "cumulative_realized_pnl": point.cumulative_realized_pnl,
    }


def _serialize_trade_pnl(trade_pnl: TradePnL) -> dict[str, float]:
    """Return the intrinsic realized-PnL fact used by an existing source point."""
    return {"realized_pnl": trade_pnl.realized_pnl}
