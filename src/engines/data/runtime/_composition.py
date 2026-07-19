"""Small explicit factory for assembling an injected Data Engine runtime."""

from dataclasses import dataclass

from src.engines.data.interfaces import DataSource
from src.engines.data.orchestration import DataEngineOrchestrator
from src.engines.data.storage import DataStore


@dataclass(frozen=True, slots=True, eq=False)
class DataEngineRuntime:
    """Identity-based bundle of injected Data Engine service objects."""

    source: DataSource
    orchestrator: DataEngineOrchestrator


def compose_data_engine_runtime(
    *,
    source: DataSource,
    data_store: DataStore | None = None,
) -> DataEngineRuntime:
    """Assemble passive runtime dependencies without executing data processing."""
    if source is None:
        raise TypeError("source must not be None")

    return DataEngineRuntime(
        source=source,
        orchestrator=DataEngineOrchestrator(data_store=data_store),
    )
