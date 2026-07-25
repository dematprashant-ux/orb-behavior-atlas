"""Immutable rejected-candidate diagnostics for successful optimization searches."""

from dataclasses import dataclass

from src.engines.backtesting.constraints import ConstraintDiagnostic
from src.engines.strategy.parameters import CandidateParameterSet

__all__ = ["ConstraintDiagnostics", "ConstraintRejection"]


@dataclass(frozen=True, slots=True)
class ConstraintRejection:
    """Retain one exact rejected candidate and its constraint diagnostic."""

    candidate: CandidateParameterSet
    diagnostic: ConstraintDiagnostic

    def __post_init__(self) -> None:
        """Require existing immutable candidate and diagnostic value objects."""
        if not isinstance(self.candidate, CandidateParameterSet):
            raise TypeError("candidate must be a CandidateParameterSet.")
        if not isinstance(self.diagnostic, ConstraintDiagnostic):
            raise TypeError("diagnostic must be a ConstraintDiagnostic.")


@dataclass(frozen=True, slots=True)
class ConstraintDiagnostics:
    """Retain rejected candidates in their deterministic encounter order."""

    rejections: tuple[ConstraintRejection, ...] = ()

    def __post_init__(self) -> None:
        """Require one immutable ordered collection without sorting or grouping."""
        if not isinstance(self.rejections, tuple):
            raise TypeError("rejections must be a tuple of ConstraintRejection values.")
        if any(
            not isinstance(rejection, ConstraintRejection)
            for rejection in self.rejections
        ):
            raise TypeError("rejections must contain only ConstraintRejection values.")
