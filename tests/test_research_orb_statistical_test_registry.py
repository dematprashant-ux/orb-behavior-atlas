"""Contract tests for the canonical immutable ORB statistical-test registry."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.research import (
    ORBStatisticalComparisonDesign,
    ORBStatisticalObservationDomain,
    ORBStatisticalTestDefinition,
    ORBStatisticalTestFamily,
    ORBStatisticalTestIdentifier,
    ORBStatisticalTestImplementationStatus,
    get_statistical_test_definition,
    list_statistical_test_definitions,
    list_statistical_test_definitions_by_family,
)


class ORBStatisticalTestRegistryTests(TestCase):
    """Verify stable metadata lookup without statistical selection or execution."""

    def test_definition_is_typed_immutable_and_deterministic(self) -> None:
        """Use a frozen value object for one planned method's stable metadata."""
        first = _definition(
            ORBStatisticalTestIdentifier.WELCH_T_TEST,
            ORBStatisticalTestFamily.PARAMETRIC,
            ORBStatisticalObservationDomain.CONTINUOUS,
            ORBStatisticalComparisonDesign.TWO_INDEPENDENT_SAMPLES,
        )
        second = _definition(
            ORBStatisticalTestIdentifier.WELCH_T_TEST,
            ORBStatisticalTestFamily.PARAMETRIC,
            ORBStatisticalObservationDomain.CONTINUOUS,
            ORBStatisticalComparisonDesign.TWO_INDEPENDENT_SAMPLES,
        )

        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        with self.assertRaises(FrozenInstanceError):
            first.test_family = ORBStatisticalTestFamily.RESAMPLING
        with self.assertRaises(TypeError):
            ORBStatisticalTestDefinition(
                "WELCH_T_TEST",  # type: ignore[arg-type]
                ORBStatisticalTestFamily.PARAMETRIC,
                ORBStatisticalObservationDomain.CONTINUOUS,
                ORBStatisticalComparisonDesign.TWO_INDEPENDENT_SAMPLES,
                ORBStatisticalTestImplementationStatus.PLANNED,
            )

    def test_metadata_enums_are_stable(self) -> None:
        """Expose only the declared observation, design, and implementation values."""
        self.assertEqual(
            tuple(ORBStatisticalObservationDomain),
            (
                ORBStatisticalObservationDomain.CONTINUOUS,
                ORBStatisticalObservationDomain.ORDINAL,
                ORBStatisticalObservationDomain.CATEGORICAL,
                ORBStatisticalObservationDomain.RESAMPLED,
            ),
        )
        self.assertEqual(
            tuple(ORBStatisticalComparisonDesign),
            (
                ORBStatisticalComparisonDesign.TWO_INDEPENDENT_SAMPLES,
                ORBStatisticalComparisonDesign.CONTINGENCY_TABLE,
                ORBStatisticalComparisonDesign.GENERIC_RESAMPLING,
            ),
        )
        self.assertEqual(
            tuple(ORBStatisticalTestImplementationStatus),
            (
                ORBStatisticalTestImplementationStatus.PLANNED,
                ORBStatisticalTestImplementationStatus.AVAILABLE,
            ),
        )

    def test_registry_is_complete_unique_ordered_and_planned(self) -> None:
        """Retain exactly one planned definition per identifier declaration order."""
        definitions = list_statistical_test_definitions()

        self.assertIsInstance(definitions, tuple)
        self.assertEqual(len(definitions), 6)
        self.assertEqual(
            tuple(definition.test_identifier for definition in definitions),
            tuple(ORBStatisticalTestIdentifier),
        )
        self.assertEqual(
            len({definition.test_identifier for definition in definitions}),
            len(ORBStatisticalTestIdentifier),
        )
        self.assertTrue(
            all(
                definition.implementation_status
                is ORBStatisticalTestImplementationStatus.PLANNED
                for definition in definitions
            )
        )

    def test_canonical_definition_mappings(self) -> None:
        """Expose each declared identifier's one authoritative metadata mapping."""
        expected = (
            (
                ORBStatisticalTestIdentifier.WELCH_T_TEST,
                ORBStatisticalTestFamily.PARAMETRIC,
                ORBStatisticalObservationDomain.CONTINUOUS,
                ORBStatisticalComparisonDesign.TWO_INDEPENDENT_SAMPLES,
            ),
            (
                ORBStatisticalTestIdentifier.MANN_WHITNEY_U,
                ORBStatisticalTestFamily.NON_PARAMETRIC,
                ORBStatisticalObservationDomain.ORDINAL,
                ORBStatisticalComparisonDesign.TWO_INDEPENDENT_SAMPLES,
            ),
            (
                ORBStatisticalTestIdentifier.CHI_SQUARE,
                ORBStatisticalTestFamily.CATEGORICAL,
                ORBStatisticalObservationDomain.CATEGORICAL,
                ORBStatisticalComparisonDesign.CONTINGENCY_TABLE,
            ),
            (
                ORBStatisticalTestIdentifier.FISHER_EXACT,
                ORBStatisticalTestFamily.CATEGORICAL,
                ORBStatisticalObservationDomain.CATEGORICAL,
                ORBStatisticalComparisonDesign.CONTINGENCY_TABLE,
            ),
            (
                ORBStatisticalTestIdentifier.PERMUTATION_TEST,
                ORBStatisticalTestFamily.RESAMPLING,
                ORBStatisticalObservationDomain.RESAMPLED,
                ORBStatisticalComparisonDesign.GENERIC_RESAMPLING,
            ),
            (
                ORBStatisticalTestIdentifier.BOOTSTRAP,
                ORBStatisticalTestFamily.RESAMPLING,
                ORBStatisticalObservationDomain.RESAMPLED,
                ORBStatisticalComparisonDesign.GENERIC_RESAMPLING,
            ),
        )

        for identifier, family, domain, design in expected:
            with self.subTest(identifier=identifier):
                definition = get_statistical_test_definition(identifier)
                self.assertIs(definition.test_family, family)
                self.assertIs(definition.observation_domain, domain)
                self.assertIs(definition.comparison_design, design)

    def test_lookup_is_typed_deterministic_and_preserves_registry_identity(self) -> None:
        """Return the one retained immutable object without mutation or copying."""
        definitions = list_statistical_test_definitions()
        for definition in definitions:
            with self.subTest(identifier=definition.test_identifier):
                first = get_statistical_test_definition(definition.test_identifier)
                second = get_statistical_test_definition(definition.test_identifier)
                self.assertIs(first, definition)
                self.assertIs(second, definition)
        with self.assertRaises(TypeError):
            get_statistical_test_definition("WELCH_T_TEST")  # type: ignore[arg-type]

    def test_family_filters_preserve_canonical_order_and_reject_invalid_inputs(self) -> None:
        """Filter only by typed family without sorting, selecting, or executing tests."""
        expected = {
            ORBStatisticalTestFamily.PARAMETRIC: (
                ORBStatisticalTestIdentifier.WELCH_T_TEST,
            ),
            ORBStatisticalTestFamily.NON_PARAMETRIC: (
                ORBStatisticalTestIdentifier.MANN_WHITNEY_U,
            ),
            ORBStatisticalTestFamily.CATEGORICAL: (
                ORBStatisticalTestIdentifier.CHI_SQUARE,
                ORBStatisticalTestIdentifier.FISHER_EXACT,
            ),
            ORBStatisticalTestFamily.RESAMPLING: (
                ORBStatisticalTestIdentifier.PERMUTATION_TEST,
                ORBStatisticalTestIdentifier.BOOTSTRAP,
            ),
        }
        for family, identifiers in expected.items():
            with self.subTest(family=family):
                definitions = list_statistical_test_definitions_by_family(family)
                self.assertIsInstance(definitions, tuple)
                self.assertEqual(
                    tuple(definition.test_identifier for definition in definitions),
                    identifiers,
                )
        with self.assertRaises(TypeError):
            list_statistical_test_definitions_by_family("PARAMETRIC")  # type: ignore[arg-type]


def _definition(
    identifier: ORBStatisticalTestIdentifier,
    family: ORBStatisticalTestFamily,
    domain: ORBStatisticalObservationDomain,
    design: ORBStatisticalComparisonDesign,
) -> ORBStatisticalTestDefinition:
    """Build one direct planned definition for immutable-model coverage."""
    return ORBStatisticalTestDefinition(
        test_identifier=identifier,
        test_family=family,
        observation_domain=domain,
        comparison_design=design,
        implementation_status=ORBStatisticalTestImplementationStatus.PLANNED,
    )
