"""Immutable finite parameter-space values for future strategy selection."""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import TypeAlias

__all__ = [
    "CandidateParameterSet",
    "DiscreteParameter",
    "ParameterDefinition",
    "ParameterSpace",
    "ParameterValue",
]

ParameterValue: TypeAlias = bool | int | float | str | Enum


@dataclass(frozen=True, slots=True)
class ParameterDefinition:
    """Describe one named finite ordered parameter domain."""

    name: str
    values: tuple[ParameterValue, ...]

    def __post_init__(self) -> None:
        """Require one non-empty homogeneous immutable value collection."""
        _validate_name(self.name)
        _validate_values(self.values)


@dataclass(frozen=True, slots=True)
class DiscreteParameter(ParameterDefinition):
    """Identify a finite explicit parameter domain without range expansion."""


@dataclass(frozen=True, slots=True)
class CandidateParameterSet(Mapping[str, ParameterValue]):
    """Represent one ordered immutable concrete assignment set."""

    assignments: tuple[tuple[str, ParameterValue], ...]

    def __post_init__(self) -> None:
        """Require ordered unique typed parameter assignments."""
        if not isinstance(self.assignments, tuple):
            raise TypeError("assignments must be a tuple of parameter assignments.")
        names: list[str] = []
        for assignment in self.assignments:
            if not isinstance(assignment, tuple) or len(assignment) != 2:
                raise TypeError("assignments must contain two-item tuples.")
            name, value = assignment
            _validate_name(name)
            _validate_value(value)
            names.append(name)
        if len(names) != len(set(names)):
            raise ValueError("assignments must not contain duplicate parameter names.")

    def __getitem__(self, name: str) -> ParameterValue:
        """Return one assigned value using ordered immutable assignment storage."""
        for configured_name, value in self.assignments:
            if configured_name == name:
                return value
        raise KeyError(name)

    def __iter__(self) -> Iterator[str]:
        """Iterate assigned names in their explicit deterministic order."""
        return (name for name, _ in self.assignments)

    def __len__(self) -> int:
        """Return the number of explicit assignments."""
        return len(self.assignments)


@dataclass(frozen=True, slots=True)
class ParameterSpace:
    """Describe an ordered immutable collection of discrete parameter domains."""

    parameters: tuple[DiscreteParameter, ...]

    def __post_init__(self) -> None:
        """Require unique ordered discrete parameter definitions."""
        if not isinstance(self.parameters, tuple):
            raise TypeError("parameters must be a tuple of DiscreteParameter values.")
        if any(not isinstance(parameter, DiscreteParameter) for parameter in self.parameters):
            raise TypeError("parameters must contain only DiscreteParameter values.")
        names = tuple(parameter.name for parameter in self.parameters)
        if len(names) != len(set(names)):
            raise ValueError("parameters must not contain duplicate parameter names.")

def _validate_name(name: str) -> None:
    """Require a non-blank stable parameter name without normalizing it."""
    if not isinstance(name, str):
        raise TypeError("parameter name must be a str.")
    if not name.strip():
        raise ValueError("parameter name must not be blank.")


def _validate_values(values: tuple[ParameterValue, ...]) -> None:
    """Require a finite non-empty homogeneous tuple without duplicate values."""
    if not isinstance(values, tuple):
        raise TypeError("values must be a tuple of ParameterValue values.")
    if not values:
        raise ValueError("values must not be empty.")
    for value in values:
        _validate_value(value)
    expected_type = type(values[0])
    if any(type(value) is not expected_type for value in values):
        raise TypeError("values must contain one compatible parameter value type.")
    if any(
        current == previous
        for index, current in enumerate(values)
        for previous in values[:index]
    ):
        raise ValueError("values must not contain duplicates.")


def _validate_value(value: ParameterValue) -> None:
    """Require one supported explicit scalar or enum-backed parameter value."""
    if isinstance(value, Enum):
        return
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("float parameter values must be finite.")
        return
    if isinstance(value, str):
        return
    raise TypeError("parameter values must be bool, int, float, str, or Enum.")
