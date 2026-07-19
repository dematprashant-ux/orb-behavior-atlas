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
Provider Payload

↓

Provider Adapter

↓

Data Engine Normalization

↓

Canonical Candles

↓

Data Source Boundary

↓

Validation

↓

Session Builder

↓

Storage and Data Quality Checks
```

Provider-specific parsing occurs inside each provider adapter. Adapters use
reusable Data Engine normalization components before returning canonical candles
through the provider-neutral data-source boundary.

## Provider Adapter Framework

Provider adapters implement the provider-neutral `DataSource` boundary. Each
adapter owns canonical request mapping, provider payload acquisition, provider
payload parsing, source timezone declaration, and M2.4 normalization. Adapters
return canonical candles only; they do not execute M2.5 validation.

Provider configuration is immutable and declarative. It contains only the
provider name, source timezone, and canonical instrument/timeframe mappings.
It must not contain credentials, transport objects, runtime state, caches, or
retry behavior.

## Canonical Normalization Boundary

Normalization accepts provider-independent values with canonical candle keys:
`timestamp`, `open`, `high`, `low`, `close`, and `volume`. Provider adapters
own provider-native parsing, field aliases, and source configuration; the Data
Engine does not maintain a provider alias registry.

Normalization assigns the requested `Instrument` and `Timeframe`, converts
timestamps to `Asia/Kolkata`, and derives `session_date` from that normalized
timestamp. It performs structural conversion only. OHLC relationships,
duplicate detection, ordering, session construction, storage, and quality
assessment remain separate responsibilities.

---

# 7. Candle Schema

Every candle must contain:

| Field | Type |
|--------|------|
| Instrument | Instrument |
| Timeframe | Timeframe |
| Timestamp | Datetime |
| Session Date | Date |
| Open | Float |
| High | Float |
| Low | Float |
| Close | Float |
| Volume | Integer |

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

Naive source timestamps require an explicit source `ZoneInfo` owned by the
provider adapter. Ambiguous or nonexistent local timestamps are rejected rather
than inferred. Provider-native timestamp formats must be parsed by the adapter
before canonical normalization.

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

## Canonical Candle Validation Boundary

Canonical validation evaluates immutable `Candle` objects after M2.4
normalization. Normalization failures raise `DataNormalizationError`; semantic
candle violations are returned as structured validation issues. Source
acquisition failures remain `DataSourceError` concerns.

M2.5 emits only error-severity issues. Warnings, quality aggregation, missing
session detection, incomplete-session detection, and gap analysis remain later
responsibilities. Duplicate and ordering checks inspect only canonical
`Candle.timestamp` values, never provider-native timestamps.

---

# 11. Missing Data Detection

The engine should detect:

- Missing candles
- Missing sessions
- Incomplete sessions
- Timestamp gaps

Quality reports should summarize all issues.

Duplicate timestamps are detected by canonical candle validation. Missing-data
detection and quality-report aggregation remain separate milestones.

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
```

Interfaces should remain stable even if implementation changes.

`get_candles()` retrieves one session's candles. `get_date_range()` retrieves
candles across an inclusive range of session dates. Both range boundaries are
required `date` values. A dedicated `DateRange` value object may be introduced
in a future milestone to encapsulate these semantics.

Validation and quality-reporting operations remain deferred until their result
models are defined.

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

Canonical normalization errors must provide deterministic, non-sensitive public
messages. They may retain their originating conversion error through exception
chaining, but must not expose provider payload contents or credentials.

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
