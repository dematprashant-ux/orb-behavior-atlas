"""Application orchestration for deterministic BANKNIFTY CSV ORB research."""

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engines.data import (
    BankNiftyM5CsvProvider,
    DataEngineExecutionRequest,
    DataEngineExecutionResult,
    DataEngineOrchestrator,
    ExecutionStatus,
    Instrument,
    Timeframe,
)
from src.engines.research.orb import (
    ORBBehaviorAtlas,
    ORBBehaviorRecord,
    build_behavior_atlas,
    build_behavior_record,
    classify_orb_behavior,
    extract_opening_range,
    find_first_escape_event,
    generate_orb_features,
    observe_post_escape,
)

__all__ = ["BankNiftyCsvOrbResearchPipeline", "ORBResearchPipelineResult"]

_ORB_DURATION = timedelta(minutes=15)


@dataclass(frozen=True, slots=True)
class ORBResearchPipelineResult:
    """Retains one canonical data execution and its completed behavior atlas."""

    data_execution: DataEngineExecutionResult
    behavior_atlas: ORBBehaviorAtlas

    def __post_init__(self) -> None:
        """Keep result children typed and failed executions free of research records."""
        if not isinstance(self.data_execution, DataEngineExecutionResult):
            raise TypeError("data_execution must be a DataEngineExecutionResult")
        if not isinstance(self.behavior_atlas, ORBBehaviorAtlas):
            raise TypeError("behavior_atlas must be an ORBBehaviorAtlas")
        if (
            self.data_execution.status is not ExecutionStatus.COMPLETED
            and len(self.behavior_atlas) != 0
        ):
            raise ValueError(
                "non-completed data execution cannot produce behavior records"
            )


class BankNiftyCsvOrbResearchPipeline:
    """Compose canonical Data Engine and ORB research capabilities without new logic."""

    def __init__(
        self,
        *,
        data_engine: DataEngineOrchestrator,
        source_timezone: ZoneInfo,
    ) -> None:
        """Configure injected data orchestration and CSV timestamp interpretation."""
        if not isinstance(data_engine, DataEngineOrchestrator):
            raise TypeError("data_engine must be a DataEngineOrchestrator")
        if not isinstance(source_timezone, ZoneInfo):
            raise TypeError("source_timezone must be a ZoneInfo")
        self._data_engine = data_engine
        self._source_timezone = source_timezone

    def run(
        self,
        csv_path: Path,
        *,
        start_date: date,
        end_date: date,
    ) -> ORBResearchPipelineResult:
        """Build canonical ORB behavior records from one BANKNIFTY M5 CSV source."""
        provider = BankNiftyM5CsvProvider(
            csv_path,
            source_timezone=self._source_timezone,
        )
        data_execution = self._data_engine.execute(
            provider,
            DataEngineExecutionRequest(
                instrument=Instrument.BANKNIFTY,
                timeframe=Timeframe.M5,
                start_date=start_date,
                end_date=end_date,
            ),
        )
        if data_execution.status is not ExecutionStatus.COMPLETED:
            return ORBResearchPipelineResult(
                data_execution=data_execution,
                behavior_atlas=build_behavior_atlas(()),
            )

        return ORBResearchPipelineResult(
            data_execution=data_execution,
            behavior_atlas=build_behavior_atlas(
                self._build_records(data_execution)
            ),
        )

    @staticmethod
    def _build_records(
        data_execution: DataEngineExecutionResult,
    ) -> tuple[ORBBehaviorRecord, ...]:
        """Delegate each complete canonical session through existing ORB operations."""
        records: list[ORBBehaviorRecord] = []
        for session in data_execution.sessions:
            try:
                opening_range = extract_opening_range(
                    session,
                    duration=_ORB_DURATION,
                )
            except ValueError:
                continue

            escape_event = find_first_escape_event(opening_range, session)
            post_escape_observation = (
                observe_post_escape(opening_range, escape_event, session)
                if escape_event is not None
                else None
            )
            behavior = classify_orb_behavior(
                opening_range,
                escape_event,
                post_escape_observation,
            )
            features = generate_orb_features(
                opening_range,
                escape_event,
                post_escape_observation,
                behavior,
            )
            records.append(
                build_behavior_record(
                    opening_range,
                    escape_event,
                    post_escape_observation,
                    behavior,
                    features,
                )
            )
        return tuple(records)
