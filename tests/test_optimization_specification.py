"""Contract tests for immutable deterministic optimization specifications."""

from dataclasses import FrozenInstanceError, dataclass, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveSelection,
    OptimizationConfiguration,
    OptimizationSpecification,
)
from src.engines.strategy import DiscreteParameter, ParameterSpace


class OptimizationSpecificationTests(TestCase):
    """Verify what-to-optimize descriptions without executing a pipeline."""

    def test_specification_is_immutable_and_retains_exact_references(self) -> None:
        parameter_space = _parameter_space()
        configuration = _configuration()
        specification = OptimizationSpecification(parameter_space, configuration)

        self.assertTrue(is_dataclass(specification))
        self.assertFalse(hasattr(specification, "__dict__"))
        self.assertIs(specification.parameter_space, parameter_space)
        self.assertIs(specification.configuration, configuration)
        with self.assertRaises(FrozenInstanceError):
            specification.parameter_space = parameter_space  # type: ignore[misc]

    def test_specification_has_deterministic_value_semantics(self) -> None:
        first = OptimizationSpecification(_parameter_space(), _configuration())
        second = OptimizationSpecification(_parameter_space(), _configuration())

        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))

    def test_specification_rejects_invalid_component_values(self) -> None:
        with self.assertRaisesRegex(TypeError, "parameter_space"):
            OptimizationSpecification(None, _configuration())  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "configuration"):
            OptimizationSpecification(
                _parameter_space(), None
            )  # type: ignore[arg-type]

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import OptimizationSpecification as PackageSpec

        self.assertIs(PackageSpec, OptimizationSpecification)


@dataclass(frozen=True, slots=True)
class _SelectionPolicy:
    """Minimal structural policy used only to describe a test configuration."""

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Return an empty immutable selection for the supplied ranking."""
        return ObjectiveSelection(ranking)


def _parameter_space() -> ParameterSpace:
    """Build one existing immutable parameter space for specification tests."""
    return ParameterSpace((DiscreteParameter("orb_minutes", (5, 15)),))


def _configuration() -> OptimizationConfiguration:
    """Build one existing immutable policy configuration for specification tests."""
    return OptimizationConfiguration(ObjectiveDirection.MAXIMIZE, _SelectionPolicy())
