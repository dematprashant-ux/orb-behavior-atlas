"""Domain-model tests for M2.2."""

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import date, datetime
import unittest

from src.engines.data import Candle, Instrument, Session, Timeframe, Weekday


class DataEngineModelTests(unittest.TestCase):
    """Verify the M2.2 model public surface and structural invariants."""

    def test_v1_market_enums_expose_only_approved_members(self) -> None:
        """Keep the v1 instrument and timeframe scope intentionally narrow."""
        self.assertEqual(list(Instrument), [Instrument.BANKNIFTY])
        self.assertEqual(list(Timeframe), [Timeframe.M5])

    def test_candle_fields_match_the_public_model_order(self) -> None:
        """Preserve the approved canonical candle field order."""
        self.assertEqual(
            [field.name for field in fields(Candle)],
            [
                "instrument",
                "timeframe",
                "timestamp",
                "session_date",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
        )

    def test_models_are_immutable_dataclasses(self) -> None:
        """Ensure the market primitives cannot be mutated after construction."""
        candle = Candle(
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            timestamp=datetime(2026, 7, 17, 9, 15),
            session_date=date(2026, 7, 17),
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.5,
            volume=1,
        )
        session = Session(
            session_date=date(2026, 7, 17),
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            weekday=Weekday.FRIDAY,
            is_weekly_expiry=False,
            is_monthly_expiry=False,
            has_holiday_gap=False,
            candles=(candle,),
        )

        self.assertTrue(is_dataclass(candle))
        self.assertTrue(is_dataclass(session))
        with self.assertRaises(FrozenInstanceError):
            candle.volume = 2


if __name__ == "__main__":
    unittest.main()
