"""Strategy Engine structural domain and pure evaluation interface."""

from src.engines.strategy.context import build_strategy_context
from src.engines.strategy.interfaces import CandidateGenerator, Strategy
from src.engines.strategy.grid import GridCandidateGenerator
from src.engines.strategy.indexing import (
    CartesianParameterSpaceIndexer,
    ParameterSpaceIndexer,
)
from src.engines.strategy.models import (
    StrategyContext,
    StrategyDecision,
    StrategyDecisionType,
)
from src.engines.strategy.orb_rule import ORBRuleStrategy
from src.engines.strategy.parameters import (
    CandidateParameterSet,
    DiscreteParameter,
    ParameterDefinition,
    ParameterSpace,
    ParameterValue,
)

__all__ = [
    "Strategy",
    "CandidateGenerator",
    "CartesianParameterSpaceIndexer",
    "GridCandidateGenerator",
    "StrategyContext",
    "StrategyDecision",
    "StrategyDecisionType",
    "ORBRuleStrategy",
    "CandidateParameterSet",
    "DiscreteParameter",
    "ParameterDefinition",
    "ParameterSpace",
    "ParameterSpaceIndexer",
    "ParameterValue",
    "build_strategy_context",
]
