"""Contract tests for M3.2 passive Data Engine runtime composition."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date
from inspect import Parameter, signature
from typing import get_type_hints
from unittest.mock import patch
import unittest

from src.engines.data import (
    DataEngineOrchestrator,
    DataEngineRuntime,
    DataSource,
    DataStore,
    compose_data_engine_runtime,
)


class DataEngineRuntimeContractTests(unittest.TestCase):
    """Verify composition wires explicit dependencies without executing them."""

    def test_public_factory_signature_is_narrow_and_typed(self) -> None:
        """Accept only an injected source and optional injected storage boundary."""
        factory_signature = signature(compose_data_engine_runtime)

        self.assertEqual(list(factory_signature.parameters), ["source", "data_store"])
        for parameter_name in ("source", "data_store"):
            self.assertIs(
                factory_signature.parameters[parameter_name].kind,
                Parameter.KEYWORD_ONLY,
            )
        self.assertEqual(
            get_type_hints(compose_data_engine_runtime),
            {
                "source": DataSource,
                "data_store": DataStore | None,
                "return": DataEngineRuntime,
            },
        )

    def test_runtime_retains_the_exact_source_without_execution(self) -> None:
        """Composition must not call injected provider or storage dependencies."""
        source = _CountingSource()
        store = _CountingStore()

        runtime = compose_data_engine_runtime(source=source, data_store=store)

        self.assertIs(runtime.source, source)
        self.assertIsInstance(runtime.orchestrator, DataEngineOrchestrator)
        self.assertEqual(source.fetch_calls, 0)
        self.assertEqual(store.store_calls, 0)
        self.assertEqual(store.load_calls, 0)

    def test_factory_passes_the_exact_store_to_the_orchestrator(self) -> None:
        """Wire optional storage directly without inspection or transformation."""
        source = _CountingSource()
        store = _CountingStore()

        with patch("src.engines.data.runtime._composition.DataEngineOrchestrator") as constructor:
            orchestrator = object()
            constructor.return_value = orchestrator

            runtime = compose_data_engine_runtime(source=source, data_store=store)

        constructor.assert_called_once_with(data_store=store)
        self.assertIs(runtime.orchestrator, orchestrator)
        self.assertIs(runtime.source, source)

    def test_runtime_is_immutable_and_identity_based(self) -> None:
        """Avoid value equality and hashing for injected service-object bundles."""
        source = _CountingSource()
        first = compose_data_engine_runtime(source=source)
        second = compose_data_engine_runtime(source=source)

        self.assertTrue(is_dataclass(first))
        self.assertIsNot(first, second)
        self.assertNotEqual(first, second)
        with self.assertRaises(FrozenInstanceError):
            first.source = _CountingSource()

    def test_none_source_is_rejected_without_runtime_protocol_inspection(self) -> None:
        """Require only the explicit non-null composition precondition."""
        with self.assertRaisesRegex(TypeError, "source must not be None"):
            compose_data_engine_runtime(source=None)


class _CountingSource:
    """Source fixture that records calls while providing no runtime behavior."""

    def __init__(self) -> None:
        self.fetch_calls = 0

    def fetch(
        self,
        *,
        instrument: object,
        timeframe: object,
        start_date: date,
        end_date: date,
    ) -> tuple[object, ...]:
        """Record an invocation if a test accidentally executes the source."""
        self.fetch_calls += 1
        return ()


class _CountingStore:
    """Store fixture that records calls while providing no persistence behavior."""

    def __init__(self) -> None:
        self.store_calls = 0
        self.load_calls = 0

    def store_session(self, request: object) -> object:
        """Record an invocation if a test accidentally persists a session."""
        self.store_calls += 1
        return None

    def load_session(self, request: object) -> object:
        """Record an invocation if a test accidentally retrieves a session."""
        self.load_calls += 1
        return None

    def load_candles(self, request: object) -> object:
        """Record an invocation if a test accidentally retrieves candles."""
        self.load_calls += 1
        return None


if __name__ == "__main__":
    unittest.main()
