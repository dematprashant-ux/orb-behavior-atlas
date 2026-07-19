# Behavior Dictionary

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines the market behaviors recognized by the ORB Behavior Atlas.

A **Behavior** is a meaningful market pattern formed by one or more Events.

Behaviors are discovered, measured, validated and eventually transformed into trading strategies.

---

# 2. Behavior Hierarchy

```
Candles

↓

Events

↓

Event Sequence

↓

Behavior

↓

Research

↓

Validated Evidence

↓

Strategy
```

---

# 3. Behavior Design Principles

Every behavior must:

- Be measurable
- Be deterministic
- Be reproducible
- Be composed of events
- Be statistically testable

---

# 4. Behavior Categories

| Category | Description |
|----------|-------------|
| Trend | Directional movement |
| Rotation | Two-sided movement |
| Acceptance | Price accepts a level |
| Rejection | Price rejects a level |
| Continuation | Move continues |
| Failure | Expected move fails |
| Compression | Price contracts |
| Expansion | Price expands |

---

# 5. Behavior Definitions

---

## Initial ORB Observation Classifications

M5.1 defines three narrow, immutable classifications from existing ORB escape
and post-escape observations: `NO_ESCAPE`, `ESCAPE_WITH_RETURN`, and
`ESCAPE_WITHOUT_RETURN`. They are not the broader behavior definitions below:
they do not determine trend, success, failure, or a trading outcome.

---

## BHV-001 — Trend Day

### Definition

Price consistently moves in one direction after ORB.

### Typical Sequence

```
Break

↓

Acceptance

↓

Continuation

↓

Target Hit
```

---

## BHV-002 — Rotation Day

### Definition

Price rotates between ORB High and ORB Low without sustained acceptance.

---

## BHV-003 — Range Day

### Definition

Price remains inside the ORB for most of the session.

---

## BHV-004 — ORB High Acceptance

### Definition

Price breaks ORB High and remains above it.

---

## BHV-005 — ORB High Rejection

### Definition

Price touches ORB High but returns below it.

---

## BHV-006 — ORB Low Acceptance

Price remains below ORB Low after breaking it.

---

## BHV-007 — ORB Low Rejection

Price rejects ORB Low and moves back upward.

---

## BHV-008 — Mid Magnet

### Definition

Price repeatedly revisits ORB Mid during the session.

---

## BHV-009 — R1 Continuation

Price reaches R1 and continues toward R2 without significant pullback.

---

## BHV-010 — S1 Continuation

Price reaches S1 and continues toward S2.

---

## BHV-011 — Failed Breakout

Break event followed immediately by Failure event.

---

## BHV-012 — Double Rejection

Two separate rejection events occur at the same level.

---

## BHV-013 — Level Flip

Broken resistance becomes support.

Broken support becomes resistance.

---

## BHV-014 — Exhaustion

Directional movement loses momentum after multiple target levels.

---

## BHV-015 — Expansion

Price volatility increases after ORB.

---

## BHV-016 — Compression

Price volatility contracts before expansion.

---

# 6. Behavior Object

Every detected behavior contains:

| Field | Description |
|--------|-------------|
| behavior_id | Unique identifier |
| behavior_name | Behavior type |
| start_time | Detection time |
| end_time | Completion time |
| confidence_score | Confidence level |
| supporting_events | Number of events |
| direction | Bullish / Bearish / Neutral |

---

# 7. Behavior Lifecycle

```
Events

↓

Candidate Behavior

↓

Statistical Analysis

↓

Validation

↓

Accepted Behavior

↓

Strategy Candidate
```

---

# 8. Detection Rules

A behavior may only be created when:

- Required events exist
- Events occur in valid order
- Time sequence is correct
- Logical consistency is maintained

---

# 9. Research Metrics

Every behavior should record:

- Sample Size
- Win Rate
- Average Move
- Average Duration
- Maximum Favorable Excursion (MFE)
- Maximum Adverse Excursion (MAE)
- Probability
- Expectancy

---

# 10. Validation Requirements

Before a behavior becomes an edge it must pass:

- Walk-forward validation
- Out-of-sample testing
- Regime testing
- Statistical significance
- Minimum sample size

---

# 11. Future Behaviors

Future versions may include:

- Liquidity Sweep
- Volatility Expansion
- ORB Trap
- News Reaction
- Trend Exhaustion
- Multi-Day Continuation
- Gap Recovery
- Gap Failure

---

# 12. Conclusion

Behaviors are the bridge between raw market events and research.

They represent repeatable market structures that can be measured, validated and eventually transformed into robust trading strategies.
