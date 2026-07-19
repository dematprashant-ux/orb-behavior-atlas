# System Architecture

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines the overall architecture of the ORB Behavior Atlas.

Its purpose is to provide a blueprint for designing, implementing, testing, and extending the platform.

Every future module, class, and function must follow this architecture.

---

# 2. Vision

The ORB Behavior Atlas is a quantitative research platform designed to discover, validate, and explain market behavior around the first 15-minute Opening Range (ORB).

The platform is research-first.

Trading strategies are outputs of validated research—not the starting point.

---

# 3. Design Principles

The architecture follows these principles.

## Research First

Research precedes implementation.

No feature should exist without a research purpose.

---

## Single Responsibility

Every module performs exactly one responsibility.

---

## Modularity

Modules communicate through well-defined interfaces.

No module should depend unnecessarily on another.

---

## Reproducibility

Every research result must be reproducible.

---

## Evidence Driven

Every conclusion must be supported by measurable evidence.

---

# 4. High-Level Architecture

```
Historical Data
        │
        ▼
 Data Engine
        │
        ▼
 ORB Engine
        │
        ▼
 Event Engine
        │
        ▼
 Behavior Engine
        │
        ▼
 Research Engine
        │
        ▼
 Statistics Engine
        │
        ▼
 Validation Engine
        │
        ▼
 Strategy Engine
```

---

# 5. Core Engines

## 5.1 Data Engine

### Responsibilities

- Import historical data
- Validate data quality
- Clean missing values
- Standardize timestamps
- Produce clean candle data

### Output

Validated intraday market data.

---

## 5.2 ORB Engine

### Responsibilities

Calculate the first 15-minute Opening Range.

Generate:

- ORB High
- ORB Low
- ORB Mid
- R1-R5
- S1-S5

### Output

ORB Object

---

## 5.3 Event Engine

### Responsibilities

Convert price action into standardized market events.

Examples:

- Touch
- Break
- Reject
- Retest
- Acceptance
- Failure

### Output

Ordered Event Sequence

---

## 5.4 Behavior Engine

### Responsibilities

Identify higher-level market behaviors from event sequences.

Examples:

- Trend Day
- Rotation Day
- Magnet Behavior
- Acceptance
- Rejection
- Continuation

### Output

Behavior Objects

---

## 5.5 Research Engine

### Responsibilities

Answer research questions using historical behavior.

Examples:

- Probability studies
- Sequence studies
- Time-based studies
- Level interaction studies

### Output

Research Results

---

## 5.6 Statistics Engine

### Responsibilities

Measure research quality.

Examples

- Sample Size
- Probability
- Mean
- Median
- Distribution
- Confidence Interval
- Expectancy

### Output

Statistical Summary

---

## 5.7 Validation Engine

### Responsibilities

Validate discovered behaviors.

Validation includes:

- Out-of-sample testing
- Walk-forward validation
- Regime analysis
- Robustness checks

### Output

Validated Evidence

---

## 5.8 Strategy Engine

### Responsibilities

Convert validated behaviors into candidate trading strategies.

This engine never creates strategies from assumptions.

Strategies must originate from validated evidence.

---

# 6. Core Objects

The platform is built around these core objects.

```
Market

↓

Trading Day

↓

ORB

↓

Level

↓

Event

↓

Behavior

↓

Hypothesis

↓

Evidence

↓

Strategy
```

Each object builds upon the previous one.

---

# 7. Data Flow

The platform follows a single-direction processing pipeline.

```
Historical Data

↓

Clean Data

↓

ORB

↓

Events

↓

Behaviors

↓

Research

↓

Statistics

↓

Validation

↓

Strategies
```

No module should bypass this pipeline.

---

# 8. Directory Structure

```
banknifty-orb-behavior-atlas/

docs/

src/
    data/
    orb/
    events/
    behavior/
    research/
    statistics/
    validation/
    strategy/

tests/

reports/

config/

scripts/

research/

assets/
```

---

# 9. Version 1.0 Scope

Version 1.0 includes:

- Historical Data Processing
- ORB Calculation
- Event Detection
- Behavior Discovery
- Statistical Analysis
- Validation Framework
- Strategy Generation

Version 1.0 excludes:

- Live Trading
- Order Execution
- Broker Integration
- Portfolio Management

---

# 10. Design Rules

The following rules are mandatory.

1. One responsibility per module.
2. No duplicated logic.
3. No hardcoded trading rules.
4. Every feature must support at least one research question.
5. Every result must be reproducible.
6. Every strategy must originate from validated evidence.

---

# 11. Future Expansion

The architecture is designed to support additional research frameworks beyond ORB.

Possible future modules include:

- VWAP Research
- Previous Day High/Low
- Weekly Levels
- Monthly Levels
- Volume Profile
- Market Profile
- Options Data
- Machine Learning Models

These additions should require minimal architectural changes.

---

# 12. Conclusion

The ORB Behavior Atlas is designed as a modular quantitative research platform.

Its primary objective is to transform historical market data into validated market knowledge.

Trading strategies are the final outcome of this research process rather than its starting point.
