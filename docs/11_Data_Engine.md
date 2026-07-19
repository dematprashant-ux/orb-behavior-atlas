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

The Session Builder constructs immutable trading sessions from canonical
`Candle` objects. It groups candles by `session_date`, `instrument`, and
`timeframe` and uses the canonical `session_date` produced by normalization.

Each session contains:

- Session date, instrument, timeframe, and weekday
- The supplied immutable candle collection
- Optional caller-supplied session metadata

Candles within a session must already be in strictly increasing canonical
timestamp order. The builder never reorders, deduplicates, validates, or
completeness-checks them. Output sessions may be sorted deterministically by
their canonical grouping key.

Session metadata is tri-state: `True` means confirmed, `False` means confirmed
not applicable, and `None` means not determined. The builder does not infer
weekly expiry, monthly expiry, holidays, or gaps. Omitted metadata remains
unknown. Metadata entries that do not match a constructed session are rejected.

Partial sessions are valid construction inputs. Exchange calendars, missing
candle/session detection, holiday and expiry inference, gap analysis, and
quality reporting remain separate responsibilities.

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

Read-only quality assessment may observe unexpected timestamp spacing within
supplied canonical sessions. It does not repair, reorder, normalize, validate,
store, or reconstruct candles or sessions.

The expected interval is derived from the canonical `Timeframe` model. Each
observation contains the previous and current canonical timestamps, along with
the expected and observed intervals. An irregular interval does not infer a
cause such as a provider failure, holiday, market closure, or missing candle.

Missing trading-day detection, holiday analysis, and market-day completeness
require a future exchange-calendar boundary. They are not quality-layer
responsibilities yet.

Duplicate timestamps and ordering remain M2.5 validation and M2.7 construction
concerns. The quality layer reports observational spacing only.

---

# 12. Data Quality Metrics

The quality layer provides immutable, read-only metrics for each supplied
session and batch report:

- Candle count
- Unexpected interval count
- First observed timestamp
- Last observed timestamp
- Total assessed sessions and candles

Quality reports preserve input session order. They do not make claims about
market-day completeness or data coverage without an exchange calendar.

---

# 13. Storage Model

The storage boundary persists canonical `Session` aggregates. A session is the
only write aggregate: its immutable metadata and canonical candle collection
are stored together. Independent candle writes are not part of the Data Engine
storage contract.

Canonical storage identities are:

```
Candle:  instrument + timeframe + timestamp
Session: session_date + instrument + timeframe
```

Session writes must preserve aggregate consistency: every candle must match the
session instrument, timeframe, and session date; candle identities must be
unique; and candle timestamps must be strictly increasing. Storage does not
repeat M2.5 OHLC validation or reconstruct sessions.

The provider-neutral `DataStore` boundary returns a requested stored session
without changing its candle order. Candle-range retrieval uses inclusive
`start_session_date` and `end_session_date` values and always returns candles
in ascending canonical timestamp order. Backend-native ordering must not cross
this boundary.

Storage format and technology remain independent of research logic. SQLite,
DuckDB, PostgreSQL, files, memory, and cloud implementations must satisfy the
same contract without changing Data Engine APIs.

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
