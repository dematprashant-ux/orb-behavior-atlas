"""Closed successful termination reasons for deterministic optimization searches."""

from enum import Enum

__all__ = ["OptimizationTerminationReason"]


class OptimizationTerminationReason(Enum):
    """Describe why a successful finite optimization search stopped."""

    SEARCH_SPACE_EXHAUSTED = "search_space_exhausted"
    EVALUATION_BUDGET_REACHED = "evaluation_budget_reached"
