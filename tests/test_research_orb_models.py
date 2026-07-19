"""Contract tests for M4.1 immutable ORB research-session domain models."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime
import ast
import unittest
from zoneinfo import ZoneInfo

from src.engines.data.models import Candle, Instrument, Session, Timeframe, Weekday
from src.engines.research import OpeningRange, ORBSession, ORBWindow
from src.engines.research.orb import OpeningRange as OrbOpeningRange


class ORBResearchModelTests(unittest.TestCase):
    """Verify the M4.1 public model surface is immutable and technology-neutral."""

    def test_public_exports_are_stable(self) -> None:
        """Expose the same model objects from Research Engine package boundaries."""
        self.assertIs(OpeningRange, OrbOpeningRange)
        self.assertTrue(ORBWindow)
        self.assertTrue(ORBSession)

    def test_models_are_frozen_slotted_dataclasses(self) -> None:
        """Keep research records immutable and free from mutable instance dictionaries."""
        window = _window()
        opening_range = _opening_range()
        orb_session = ORBSession(_session(), opening_range)

        self.assertTrue(all(is_dataclass(model) for model in (window, opening_range, orb_session)))
        self.assertFalse(hasattr(window, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            opening_range.high = 103.0

    def test_domain_values_have_deterministic_value_equality(self) -> None:
        """Treat equal observed facts as equal immutable research values."""
        self.assertEqual(_window(), _window())
        self.assertEqual(_opening_range(), _opening_range())
        self.assertEqual(
            ORBSession(_session(), _opening_range()),
            ORBSession(_session(), _opening_range()),
        )

    def test_valid_construction_reuses_the_canonical_session_type(self) -> None:
        """Anchor ORB research to the existing immutable Data Engine Session model."""
        session = _session()
        orb_session = ORBSession(session, _opening_range())

        self.assertIs(orb_session.session, session)
        self.assertEqual(
            orb_session.opening_range.window.start_timestamp.tzinfo,
            ZoneInfo("Asia/Kolkata"),
        )
        self.assertEqual(orb_session.opening_range.high, 102.0)

    def test_intrinsic_window_and_range_invariants_fail_deterministically(self) -> None:
        """Reject only local impossible model values without market-behavior checks."""
        timezone = ZoneInfo("Asia/Kolkata")
        start = datetime(2026, 7, 17, 9, 15, tzinfo=timezone)
        end = datetime(2026, 7, 17, 9, 30, tzinfo=timezone)

        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            ORBWindow(datetime(2026, 7, 17, 9, 15), end)
        with self.assertRaisesRegex(ValueError, "must not precede"):
            ORBWindow(end, start)
        with self.assertRaisesRegex(ValueError, "must not be below"):
            OpeningRange(
                window=_window(),
                open=100.0,
                high=99.0,
                low=102.0,
                close=101.0,
                candles=(_candle(),),
            )

    def test_models_do_not_depend_on_forbidden_layers_or_libraries(self) -> None:
        """Keep M4.1 independent from providers, storage, and analytical tooling."""
        module_path = "src/engines/research/orb/models.py"
        with open(module_path, encoding="utf-8") as source_file:
            tree = ast.parse(source_file.read())

        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_modules.update(
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )

        forbidden_fragments = (
            "pandas",
            "numpy",
            "providers",
            "storage",
            "orchestration",
        )
        self.assertFalse(
            any(
                fragment in imported_module
                for imported_module in imported_modules
                for fragment in forbidden_fragments
            )
        )


def _window() -> ORBWindow:
    """Create an observed timezone-aware opening-range timestamp window."""
    timezone = ZoneInfo("Asia/Kolkata")
    return ORBWindow(
        start_timestamp=datetime(2026, 7, 17, 9, 15, tzinfo=timezone),
        end_timestamp=datetime(2026, 7, 17, 9, 30, tzinfo=timezone),
    )


def _session() -> Session:
    """Create a canonical session reference without adding market calculations."""
    return Session(
        session_date=date(2026, 7, 17),
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        weekday=Weekday.FRIDAY,
        is_weekly_expiry=None,
        is_monthly_expiry=None,
        has_holiday_gap=None,
        candles=(),
    )


def _opening_range() -> OpeningRange:
    """Create observed opening-range facts without performing extraction."""
    return OpeningRange(
        window=_window(),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        candles=(_candle(),),
    )


def _candle() -> Candle:
    """Create one canonical candle as immutable observed range evidence."""
    return Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=datetime(2026, 7, 17, 9, 15, tzinfo=ZoneInfo("Asia/Kolkata")),
        session_date=date(2026, 7, 17),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=1,
    )


if __name__ == "__main__":
    unittest.main()
