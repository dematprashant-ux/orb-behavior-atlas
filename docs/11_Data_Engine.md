# Data Engine

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

The Data Engine is responsible for acquiring, validating, normalizing, and serving all market data used throughout the ORB Behavior Atlas.

It is the foundation of the platform. Every downstream engine depends on the quality and consistency of the data it provides.

---

# 2. Responsibilities

The Data Engine is responsible for:

- Market data acquisition
- Data normalization
- Data validation
- Session construction
- Timezone conversion
- Corporate action handling (if applicable)
- Missing data detection
- Data quality reporting
- Data storage
- Data retrieval

---

# 3. Supported Instruments

Version 1.0 supports:

- BANKNIFTY Index

Future versions may include:

- NIFTY 50
- FINNIFTY
- MIDCPNIFTY
- NSE Stocks
- Options
- Futures
- Global indices

---

# 4. Supported Timeframes

Primary research timeframe:

- 5 Minute

Supported aggregation:

- 1 Minute
- 5 Minute
- 15 Minute
- 30 Minute
- 60 Minute
- Daily

---

# 5. Data Sources

Each source must implement the same interface.

Supported providers may include:

- Dhan API
- NSE Historical Data
- CSV Import
- Parquet Files

The source should be interchangeable without affecting downstream engines.

---

# 6. Data Pipeline

```
Market Data Source

↓

Download

↓

Validation

↓

Normalization

↓

Session Builder

↓

Storage

↓

Data Quality Checks

↓

Research Engine
```

---

# 7. Candle Schema

Every candle must contain:

| Field | Type |
|--------|------|
| Timestamp | Datetime |
| Open | Float |
| High | Float |
| Low | Float |
| Close | Float |
| Volume | Integer |
| Session Date | Date |
| Timeframe | String |

---

# 8. Time Management

All timestamps should be stored using a consistent internal format.

Trading session timezone:

```
Asia/Kolkata
```

Session hours:

```
09:15

↓

15:30
```

Timezone conversion should occur only once during ingestion.

---

# 9. Session Builder

The Session Builder groups candles into trading days.

Each session contains:

- Session date
- Opening candle
- Closing candle
- Total candles
- Trading duration

---

# 10. Data Validation Rules

Each candle must satisfy:

- High ≥ Open
- High ≥ Close
- High ≥ Low
- Low ≤ Open
- Low ≤ Close
- Non-negative volume
- Valid timestamp
- No duplicate timestamps

Invalid records should be flagged.

---

# 11. Missing Data Detection

The engine should detect:

- Missing candles
- Duplicate candles
- Missing sessions
- Incomplete sessions
- Timestamp gaps

Quality reports should summarize all issues.

---

# 12. Data Quality Metrics

Track:

- Missing candle count
- Duplicate count
- Invalid OHLC count
- Session completeness
- Total observations
- Data coverage %

These metrics should be available to downstream engines.

---

# 13. Storage Model

Recommended structure:

```
Instrument

↓

Timeframe

↓

Trading Session

↓

Candles
```

Storage format should remain independent of research logic.

---

# 14. Public Interfaces

The Data Engine should expose functions equivalent to:

```
load_data()

get_session()

get_candles()

get_date_range()

validate_data()

quality_report()
```

Interfaces should remain stable even if implementation changes.

---

# 15. Error Handling

The engine should detect and report:

- Missing files
- API failures
- Corrupted records
- Invalid timestamps
- Unsupported instruments
- Unsupported timeframes

Errors should be descriptive and logged.

---

# 16. Performance Goals

The engine should prioritize:

- Deterministic behavior
- Reproducibility
- Fast retrieval
- Low memory usage
- Scalable architecture

Performance optimizations must never compromise data integrity.

---

# 17. Future Enhancements

Future versions may include:

- Incremental updates
- Live market streaming
- Multi-provider synchronization
- Automatic retry logic
- Data versioning
- Metadata catalog
- Distributed storage support

---

# 18. Conclusion

The Data Engine is the trusted entry point for all market data within the ORB Behavior Atlas.

By enforcing consistent ingestion, validation, and storage standards, it provides reliable data for every subsequent engine and ensures the integrity of all research conducted on the platform.
