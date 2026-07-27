"""Canonical immutable metadata registry for planned ORB statistical tests."""

from src.engines.research.orb.models import (
    ORBStatisticalComparisonDesign,
    ORBStatisticalObservationDomain,
    ORBStatisticalTestDefinition,
    ORBStatisticalTestFamily,
    ORBStatisticalTestIdentifier,
    ORBStatisticalTestImplementationStatus,
)

__all__ = [
    "get_statistical_test_definition",
    "list_statistical_test_definitions",
    "list_statistical_test_definitions_by_family",
]

_STATISTICAL_TEST_DEFINITIONS = (
    ORBStatisticalTestDefinition(
        test_identifier=ORBStatisticalTestIdentifier.WELCH_T_TEST,
        test_family=ORBStatisticalTestFamily.PARAMETRIC,
        observation_domain=ORBStatisticalObservationDomain.CONTINUOUS,
        comparison_design=ORBStatisticalComparisonDesign.TWO_INDEPENDENT_SAMPLES,
        implementation_status=ORBStatisticalTestImplementationStatus.PLANNED,
    ),
    ORBStatisticalTestDefinition(
        test_identifier=ORBStatisticalTestIdentifier.MANN_WHITNEY_U,
        test_family=ORBStatisticalTestFamily.NON_PARAMETRIC,
        observation_domain=ORBStatisticalObservationDomain.ORDINAL,
        comparison_design=ORBStatisticalComparisonDesign.TWO_INDEPENDENT_SAMPLES,
        implementation_status=ORBStatisticalTestImplementationStatus.PLANNED,
    ),
    ORBStatisticalTestDefinition(
        test_identifier=ORBStatisticalTestIdentifier.CHI_SQUARE,
        test_family=ORBStatisticalTestFamily.CATEGORICAL,
        observation_domain=ORBStatisticalObservationDomain.CATEGORICAL,
        comparison_design=ORBStatisticalComparisonDesign.CONTINGENCY_TABLE,
        implementation_status=ORBStatisticalTestImplementationStatus.PLANNED,
    ),
    ORBStatisticalTestDefinition(
        test_identifier=ORBStatisticalTestIdentifier.FISHER_EXACT,
        test_family=ORBStatisticalTestFamily.CATEGORICAL,
        observation_domain=ORBStatisticalObservationDomain.CATEGORICAL,
        comparison_design=ORBStatisticalComparisonDesign.CONTINGENCY_TABLE,
        implementation_status=ORBStatisticalTestImplementationStatus.PLANNED,
    ),
    ORBStatisticalTestDefinition(
        test_identifier=ORBStatisticalTestIdentifier.PERMUTATION_TEST,
        test_family=ORBStatisticalTestFamily.RESAMPLING,
        observation_domain=ORBStatisticalObservationDomain.RESAMPLED,
        comparison_design=ORBStatisticalComparisonDesign.GENERIC_RESAMPLING,
        implementation_status=ORBStatisticalTestImplementationStatus.PLANNED,
    ),
    ORBStatisticalTestDefinition(
        test_identifier=ORBStatisticalTestIdentifier.BOOTSTRAP,
        test_family=ORBStatisticalTestFamily.RESAMPLING,
        observation_domain=ORBStatisticalObservationDomain.RESAMPLED,
        comparison_design=ORBStatisticalComparisonDesign.GENERIC_RESAMPLING,
        implementation_status=ORBStatisticalTestImplementationStatus.PLANNED,
    ),
)


def get_statistical_test_definition(
    test_identifier: ORBStatisticalTestIdentifier,
) -> ORBStatisticalTestDefinition:
    """Return the one canonical immutable definition for a typed identifier."""
    if not isinstance(test_identifier, ORBStatisticalTestIdentifier):
        raise TypeError("test_identifier must be an ORBStatisticalTestIdentifier")
    for definition in _STATISTICAL_TEST_DEFINITIONS:
        if definition.test_identifier is test_identifier:
            return definition
    raise ValueError("test_identifier is not registered")


def list_statistical_test_definitions() -> tuple[ORBStatisticalTestDefinition, ...]:
    """Return all canonical definitions in test-identifier declaration order."""
    return _STATISTICAL_TEST_DEFINITIONS


def list_statistical_test_definitions_by_family(
    test_family: ORBStatisticalTestFamily,
) -> tuple[ORBStatisticalTestDefinition, ...]:
    """Return canonical definitions of one typed family in registry order."""
    if not isinstance(test_family, ORBStatisticalTestFamily):
        raise TypeError("test_family must be an ORBStatisticalTestFamily")
    return tuple(
        definition
        for definition in _STATISTICAL_TEST_DEFINITIONS
        if definition.test_family is test_family
    )
