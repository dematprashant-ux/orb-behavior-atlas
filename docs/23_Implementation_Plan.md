# Implementation Plan

**Project:** ORB Behavior Atlas  
**Document Version:** 1.1
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-19

---

# 1. Purpose

The Implementation Plan defines the roadmap for converting the documented architecture of the ORB Behavior Atlas into a production-grade software platform.

It specifies the order in which components are implemented, tested, validated, and integrated.

This document governs implementation only.

---

# 2. Development Philosophy

Development follows a strict progression:

```
Architecture

↓

Implementation

↓

Unit Testing

↓

Integration Testing

↓

Validation

↓

Documentation

↓

Release
```

Each stage must be completed before progressing.

---

# 3. Guiding Principles

Implementation must always be:

- Modular
- Deterministic
- Reproducible
- Testable
- Version Controlled
- Documented

No feature should bypass testing or documentation.

---

# 4. Implementation Sequence

Modules should be implemented in the following order:

1. Data Engine
2. ORB Engine
3. Event Engine
4. Behavior Engine
5. Research Engine
6. Validation Engine
7. Strategy Engine
8. Backtesting Framework
9. Portfolio Engine
10. Live Execution Engine
11. Monitoring & Observability

Each module depends only on previously completed modules.

---

# 5. Phase 1 — Foundation

Deliverables:

- Repository setup
- Development environment
- Configuration system
- Logging framework
- Project structure
- CI configuration

Definition of Done:

Project builds successfully.

---

# 6. Phase 2 — Core Engines

## M2.1 — Data Engine Architecture

### Objective

Establish the Data Engine as a stable architectural boundary before implementing
market-data behavior. This milestone defines how the engine is organized and
how downstream engines depend on it; it does not process market data.

### Scope

M2.1 establishes:

- The `src/engines/data/` package structure
- Focused module boundaries within the Data Engine
- The public API surface for future Data Engine operations
- Interfaces and protocols for data sources and data access
- A Data Engine-specific exception hierarchy
- Explicit public exports
- One-way dependency layout between `core`, the Data Engine, and downstream
  engines

### Explicit Exclusions

M2.1 must not implement:

- Domain models
- Validation logic
- Session construction
- Data providers
- Data storage
- A data quality engine

### Acceptance Criteria

M2.1 is complete when:

- The Data Engine package boundary is present and importable
- Its public contracts are explicit, typed, documented, and exported from a
  stable entry point
- Source and access abstractions do not depend on a concrete provider,
  persistence mechanism, or downstream engine
- The exception hierarchy is available for later Data Engine milestones
- Dependencies flow inward from downstream engines to the Data Engine and from
  the Data Engine to shared `core` components only
- No market-data behavior is introduced

### Deferred Milestones

The following responsibilities remain deferred to subsequent Data Engine
milestones: domain modeling, ingestion, normalization, validation, session
construction, storage, retrieval behavior, missing-data detection, and quality
reporting.

## M2.2 — Data Engine Domain Models

### Objective

Define the immutable, provider-neutral market-data models required for the
v1 BANKNIFTY five-minute research scope.

### Scope

- Typed `Instrument`, `Timeframe`, and `Weekday` enumerations
- Immutable `Candle` and `Session` models
- Stable package exports and structural model tests

### Explicit Exclusions

- Additional instruments or timeframes
- Providers, persistence, identifiers, validation, normalization, and quality
  reporting
- Session construction, timezone conversion, derived fields, and business
  logic
- Models owned by downstream engines

### Acceptance Criteria

M2.2 is complete when the public package exports immutable, typed models for
the documented BANKNIFTY five-minute candle and session structures, without
introducing market-data behavior.

## M2.3 — Data Engine Typed Interfaces

### Objective

Refine the public Data Engine protocols around canonical market-data models and
define the provider boundary without implementing market-data behavior.

### Scope

- Typed `DataSource`, `DataAccess`, and `DataEngine` protocol signatures
- Provider-boundary definition and contract tests
- Directly affected public exports and Data Engine documentation

### Explicit Exclusions

- Providers, normalization, validation, storage, sessions, and quality
  reporting
- Undefined validation and quality-result contracts
- New placeholder packages or directories

### Date Range Design Note

M2.3 uses required inclusive `start_date` and `end_date` parameters of type
`date`. A dedicated `DateRange` value object may encapsulate these semantics in
a future milestone; it is not introduced in M2.3.

### Acceptance Criteria

M2.3 is complete when the public protocols use canonical `Candle`, `Session`,
`Instrument`, and `Timeframe` types; provider adapters are documented as
returning canonical candles; and validation/quality operations remain deferred
until their result models are defined.

## M2.4 — Reusable Canonical Candle Normalization

### Objective

Establish the internal Data Engine normalization boundary that converts
provider-independent candle values into canonical immutable `Candle` objects.

### Scope

- Reusable canonical candle normalization functions
- `DataNormalizationError` in the Data Engine exception hierarchy
- Private timestamp and numeric normalization helpers
- Contract tests and directly affected Data Engine documentation

Provider adapters remain responsible for provider-specific parsing and field
mapping before calling normalization. The normalizer accepts canonical-keyed,
provider-independent values and assigns `Instrument`, `Timeframe`, and a
session date derived from the normalized `Asia/Kolkata` timestamp.

### Explicit Exclusions

- Concrete providers or provider adapters
- Provider payload parsing and alias registries
- Candle validation, duplicate detection, sessions, storage, retrieval, and
  quality reporting
- Changes to the M2.3 public protocols

### Acceptance Criteria

M2.4 is complete when adapters have a reusable internal component that creates
canonical candles with deterministic, non-sensitive normalization errors,
without introducing provider behavior or downstream Data Engine concerns.

## M2.5 — Canonical Candle Validation

### Objective

Report semantic validity of canonical immutable candles through structured,
immutable validation results without transforming or rejecting input data.

### Scope

- Immutable validation result models and stable validation codes
- Single-candle semantic validation
- Batch duplicate and timestamp-order checks on canonical timestamps
- Contract tests and directly affected Data Engine documentation

M2.5 emits only `ERROR` severity. `WARNING` is reserved for later milestones.
Provider-native timestamps are outside this boundary: duplicate and ordering
checks operate only on canonical `Candle.timestamp` values produced by M2.4.

### Explicit Exclusions

- Providers, source I/O, and normalization changes
- Session construction, storage, retrieval, and missing-data detection
- Gap analysis, quality aggregation, dashboards, and strategy logic
- Changes to M2.3 public protocols

### Acceptance Criteria

M2.5 is complete when all documented candle-level semantic rules are reported
deterministically as structured results, while acquisition and normalization
failures remain exception-based concerns at their existing boundaries.

## M2.6 — Provider Adapter Framework

### Objective

Establish the transport-neutral framework through which future external market
data providers implement the existing `DataSource` contract.

### Scope

- Immutable declarative `ProviderConfig` and canonical request mappings
- `ProviderAdapter` protocol and reusable `BaseProviderAdapter`
- Provider payload acquisition and parsing extension points
- M2.4 canonical normalization integration
- Contract tests and directly affected Data Engine documentation

Provider adapters stop after canonical normalization and return `Candle`
objects through `DataSource.fetch()`. M2.5 validation remains outside this
framework and is not executed by adapters.

### Explicit Exclusions

- Concrete providers, HTTP, REST, WebSockets, authentication, retries, and
  caching
- Validation execution, sessions, storage, retrieval, and quality reporting
- Provider runtime state, transport objects, credentials, or mutable config
- Changes to the M2.3 `DataSource` public retrieval interface

### Acceptance Criteria

M2.6 is complete when a future provider can map requests, acquire and parse
payloads through protected extension points, normalize canonical candles, and
return them through the unchanged provider-neutral source contract.

## M2.7 — Session Construction & Trading-Day Boundaries

### Objective

Construct immutable trading sessions from canonical candles without adding
calendar, completeness, quality, or storage behavior.

### Scope

- Group canonical candles by `session_date`, `instrument`, and `timeframe`
- Preserve the supplied candle order after requiring strictly increasing
  canonical timestamps
- Return deterministically ordered immutable `Session` objects
- Support immutable tri-state `SessionMetadata` supplied by the caller
- Reject metadata entries that do not correspond to a constructed session

### Explicit Exclusions

- Validation execution, normalization changes, providers, storage, and
  retrieval
- Exchange calendars, holidays, expiry inference, gap analysis, and session
  completeness analysis
- Quality reporting, ORB logic, analytics, and strategy behavior

### Acceptance Criteria

M2.7 is complete when callers can construct partial immutable sessions from
canonical candles while preserving each group's input order, representing
unknown session metadata as `None`, and receiving deterministic failures for
duplicate or descending timestamps and unmatched metadata keys.

## M2.8 — Data Storage Boundary

### Objective

Define a technology-neutral persistence boundary for canonical sessions and
candles without selecting or implementing a storage backend.

### Scope

- Immutable canonical storage identities, requests, and results
- A single `DataStore` protocol
- Session-only write aggregation and canonical candle retrieval
- Storage aggregate-consistency checks and a storage exception hierarchy
- Contract tests and directly affected Data Engine documentation

### Explicit Exclusions

- Databases, files, serialization, migrations, indexes, caching, cloud
  storage, authentication, and scheduling
- Independent candle writes, overwrite, upsert, deletion, replacement, and
  batch-write behavior
- Changes to `DataSource`, `DataAccess`, or `DataEngine`
- Validation execution, normalization, session reconstruction, quality
  reporting, analytics, ORB logic, and strategy behavior

### Acceptance Criteria

M2.8 is complete when storage implementations can depend on a single public,
technology-neutral protocol with immutable canonical values; candle loads have
inclusive session-date ranges and deterministic timestamp ordering; and
malformed session aggregates and existing storage identities have defined,
separate failure semantics.

## M2.9 — Data Quality Assessment

### Objective

Provide read-only, deterministic quality observations for canonical constructed
sessions without repairing, validating, reconstructing, or persisting data.

### Scope

- Immutable quality models, codes, severities, metrics, and reports
- Single-session and ordered batch assessment APIs
- Observation of timestamp spacing against each timeframe's canonical duration
- Contract tests and directly affected Data Engine documentation

### Explicit Exclusions

- Normalization, semantic validation, session construction, storage, retrieval,
  repair, sorting, deduplication, and reconstruction
- Exchange calendars, holidays, expiry logic, missing trading-day detection,
  and market-day completeness inference
- Analytics, ORB logic, strategy logic, and downstream decision-making

### Acceptance Criteria

M2.9 is complete when immutable constructed sessions can be assessed without
mutation; unexpected timestamp spacing is reported as self-contained,
deterministically ordered observations; and unsupported timeframe durations
fail as deterministic programming or configuration errors.

## M3.1 — Data Engine Orchestration

### Objective

Compose completed Data Engine capabilities into one deterministic application
workflow without duplicating provider, validation, construction, quality, or
storage behavior.

### Scope

- Immutable execution request, result, status, and failure-stage models
- One `DataEngineOrchestrator` application service
- Fetch, validate, reject, construct, assess, and optional store coordination
- Contract tests and directly affected Data Engine documentation

### Explicit Exclusions

- Provider registries, dependency-injection containers, retrieval APIs, storage
  backends, retries, rollback, transactions, and concrete persistence behavior
- Normalization changes, validation-rule changes, repair, reconstruction,
  analytics, ORB logic, strategy logic, and live execution

### Acceptance Criteria

M3.1 is complete when every execution follows the same deterministic sequence:
canonical fetch, semantic validation, rejection of any invalid candle,
session construction, quality assessment, optional storage, and immutable
terminal result reporting as `COMPLETED`, `REJECTED`, or `FAILED`.

## M3.2 — Runtime Composition & Dependency Wiring

### Objective

Provide one small, explicit composition boundary that assembles the injected
Data Engine source, optional storage boundary, and orchestrator without
executing the pipeline.

### Scope

- Identity-based immutable `DataEngineRuntime` bundle
- `compose_data_engine_runtime()` factory
- Explicit wiring of `DataSource`, optional `DataStore`, and
  `DataEngineOrchestrator`
- Contract tests and directly affected Data Engine documentation

### Explicit Exclusions

- Runtime execution methods, provider or storage construction, environment
  loading, configuration parsing, registries, plugins, DI containers, service
  locators, lifecycle management, health checks, and retrieval
- Analytics, ORB logic, strategy logic, and downstream engine work

### Acceptance Criteria

M3.2 is complete when callers can inject a non-null `DataSource` and optional
`DataStore` into a passive immutable runtime bundle; composition performs no
I/O, discovery, configuration loading, or pipeline execution.

Implement:

- Data Engine
- ORB Engine
- Event Engine

Testing:

- Unit tests
- Integration tests
- Historical replay

Definition of Done:

Reliable event generation.

---

# 7. Phase 3 — Research Layer

Implement:

- Behavior Engine
- Research Engine
- Research Database
- Hypothesis Register

Testing:

- Statistical verification
- Event consistency
- Research reproducibility

Definition of Done:

Research pipeline operational.

---

# 8. Phase 4 — Validation Layer

Implement:

- Validation Engine
- Confidence scoring
- Evidence scoring
- Walk-forward validation
- Regime testing

Testing:

- Historical validation
- Statistical consistency

Definition of Done:

Validated edges produced.

---

# 9. Phase 5 — Strategy Layer

Implement:

- Strategy Engine
- Rule compiler
- Position sizing
- Strategy configuration

Testing:

- Signal verification
- Rule consistency
- Regression tests

Definition of Done:

Strategies generated from validated edges.

---

# 10. Phase 6 — Backtesting

Implement:

- Simulation engine
- Cost model
- Slippage model
- Reporting

Testing:

- Historical replay
- Accounting validation
- Bias detection

Definition of Done:

Accurate strategy evaluation.

---

# 11. Phase 7 — Portfolio

Implement:

- Portfolio Engine
- Allocation engine
- Exposure management
- Risk controls

Testing:

- Portfolio accounting
- Allocation correctness
- Risk enforcement

Definition of Done:

Stable portfolio management.

---

# 12. Phase 8 — Live Trading

Implement:

- Broker interface
- Live Execution Engine
- Position synchronization
- Order management

Testing:

- Paper trading
- Connectivity testing
- Failure recovery

Definition of Done:

Production-ready execution.

---

# 13. Phase 9 — Monitoring

Implement:

- Metrics collection
- Dashboard
- Alerting
- Audit logs

Testing:

- Alert generation
- Health monitoring
- Observability validation

Definition of Done:

Complete operational visibility.

---

# 14. Testing Strategy

Every module requires:

- Unit Tests
- Integration Tests
- Regression Tests
- Performance Tests
- Acceptance Tests

Testing is mandatory before integration.

---

# 15. Documentation Requirements

Every implemented module must include:

- API documentation
- Configuration guide
- Usage examples
- Design notes
- Test results
- Version history

Documentation is part of the implementation.

---

# 16. Coding Standards

Code should be:

- Readable
- Modular
- Type-safe where applicable
- Consistently formatted
- Fully documented

Coding standards apply across all modules.

---

# 17. Release Strategy

Each release should include:

- Version number
- Release notes
- Migration notes (if required)
- Test summary
- Documentation updates

Every release must be reproducible.

---

# 18. Milestone Checklist

Major milestones:

- Foundation Complete
- Core Engines Complete
- Research Platform Complete
- Validation Complete
- Strategy Engine Complete
- Backtesting Complete
- Portfolio Complete
- Live Trading Complete
- Monitoring Complete
- Production Release

Each milestone requires formal acceptance.

---

# 19. Definition of Done (DoD)

A feature is complete only when:

- Implementation finished
- Tests passing
- Documentation updated
- Code reviewed
- Version controlled
- Acceptance criteria satisfied

Partial completion is not considered complete.

---

# 20. Risk Management

Implementation risks include:

- Architecture drift
- Untested code
- Data inconsistencies
- Integration failures
- Documentation gaps

Risks should be identified and resolved before release.

---

# 21. Future Enhancements

Future implementation phases may include:

- Distributed processing
- Cloud-native deployment
- Multi-broker support
- AI-assisted research
- Cross-asset expansion
- Automated deployment pipelines

Enhancements must remain compatible with the core architecture.

---

# 22. Conclusion

The Implementation Plan provides the execution blueprint for building the ORB Behavior Atlas.

By following a disciplined sequence of implementation, testing, validation, documentation, and release, the platform can evolve into a reliable, maintainable, and production-grade quantitative research and trading system.
