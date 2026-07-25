"""Deterministic multi-position portfolio cash and lifecycle transitions."""

from dataclasses import dataclass

from src.engines.portfolio.allocation import (
    AllocationDecision,
    AllocationRequest,
    CapitalAllocationPolicy,
)
from src.engines.portfolio.builders import (
    build_portfolio_position,
    build_portfolio_snapshot,
)
from src.engines.portfolio.events import (
    PortfolioCloseEvent,
    PortfolioEvent,
    PortfolioOpenEvent,
)
from src.engines.portfolio.models import PortfolioPosition, PortfolioSnapshot

__all__ = ["StandardPortfolioEngine"]


@dataclass(frozen=True, slots=True)
class StandardPortfolioEngine:
    """Apply ordered explicit events using an injected allocation policy.

    The engine preserves supplied event order. It does not sort, retry,
    calculate transaction costs, mark positions to market, or call analytics.
    Quantity is a whole integer because the existing completed-trade contract
    uses integer quantities; remainder below one entry-price unit remains cash.
    """

    allocation_policy: CapitalAllocationPolicy

    def __post_init__(self) -> None:
        """Require one injected policy object without executing it."""
        if self.allocation_policy is None:
            raise TypeError("allocation_policy must not be None.")

    def process(
        self,
        initial_snapshot: PortfolioSnapshot,
        events: tuple[PortfolioEvent, ...],
    ) -> tuple[PortfolioSnapshot, ...]:
        """Return immutable states from the initial snapshot through each event."""
        if not isinstance(initial_snapshot, PortfolioSnapshot):
            raise TypeError("initial_snapshot must be a PortfolioSnapshot.")
        if not isinstance(events, tuple):
            raise TypeError("events must be a tuple of PortfolioEvent values.")
        if any(
            not isinstance(event, (PortfolioOpenEvent, PortfolioCloseEvent))
            for event in events
        ):
            raise TypeError("events must contain only PortfolioEvent values.")

        snapshots = [initial_snapshot]
        current_snapshot = initial_snapshot
        for event in events:
            if event.timestamp < current_snapshot.timestamp:
                raise ValueError("event timestamps must not decrease.")
            if isinstance(event, PortfolioOpenEvent):
                current_snapshot = self._open(current_snapshot, event)
            else:
                current_snapshot = self._close(current_snapshot, event)
            snapshots.append(current_snapshot)
        return tuple(snapshots)

    def _open(
        self,
        snapshot: PortfolioSnapshot,
        event: PortfolioOpenEvent,
    ) -> PortfolioSnapshot:
        """Allocate, size, and deduct one new whole-unit active position."""
        if any(
            position.position_id == event.position_id
            for position in snapshot.positions
        ):
            raise ValueError("position_id is already active.")
        decision = self.allocation_policy.allocate(
            AllocationRequest(snapshot.available_cash)
        )
        if not isinstance(decision, AllocationDecision):
            raise TypeError("allocation_policy must return an AllocationDecision.")
        if decision.allocated_capital > snapshot.available_cash:
            raise ValueError("allocation must not exceed available cash.")
        quantity = int(decision.allocated_capital / event.entry_price)
        if quantity <= 0:
            raise ValueError("allocation must fund at least one whole position unit.")
        entry_capital = quantity * event.entry_price
        position = build_portfolio_position(
            event.position_id,
            event.instrument,
            event.side,
            quantity,
            event.entry_price,
            event.timestamp,
        )
        return build_portfolio_snapshot(
            event.timestamp,
            snapshot.available_cash - entry_capital,
            snapshot.positions + (position,),
        )

    def _close(
        self,
        snapshot: PortfolioSnapshot,
        event: PortfolioCloseEvent,
    ) -> PortfolioSnapshot:
        """Restore exit proceeds once and remove the selected active position."""
        position = _active_position(snapshot.positions, event.position_id)
        if position is None:
            raise ValueError("position_id is not active.")
        exit_proceeds = position.quantity * event.exit_price
        return build_portfolio_snapshot(
            event.timestamp,
            snapshot.available_cash + exit_proceeds,
            tuple(
                candidate
                for candidate in snapshot.positions
                if candidate.position_id != event.position_id
            ),
        )


def _active_position(
    positions: tuple[PortfolioPosition, ...],
    position_id: str,
) -> PortfolioPosition | None:
    """Return one active identity without changing caller-supplied ordering."""
    return next(
        (
            position
            for position in positions
            if position.position_id == position_id
        ),
        None,
    )
