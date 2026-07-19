"""Explicit passive runtime composition for Data Engine dependencies."""

from src.engines.data.runtime._composition import (
    DataEngineRuntime,
    compose_data_engine_runtime,
)

__all__ = ["DataEngineRuntime", "compose_data_engine_runtime"]
