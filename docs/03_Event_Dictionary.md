# Event Dictionary

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines every market event recognized by the ORB Behavior Atlas.

An **Event** is an atomic market action detected from price interacting with ORB-derived levels.

Events are the foundation for behavior discovery, statistics, validation, and strategy generation.

---

# 2. Event Design Principles

Every event must:

- Have one clear definition.
- Be deterministic.
- Be reproducible.
- Be independent of opinions.
- Be detectable from historical data.

---

# 3. Event Hierarchy

```
Price

↓

Level Interaction

↓

Event

↓

Event Sequence

↓

Behavior
```

---

# 4. Event Categories

| Category | Description |
|----------|-------------|
| Interaction | Price reaches a level |
| Confirmation | Price confirms a move |
| Failure | Expected move fails |
| Transition | Price moves between levels |
| Completion | Target behavior completes |

---

# 5. Event Definitions

---

## EVT-001 — Touch

### Definition

Price reaches a level for the first time.

### Rule

```
High >= Level
AND
Low <= Level
```

### Output

Touch Event

---

## EVT-002 — First Touch

First touch of a level during the trading session.

Only one First Touch may exist for each level.

---

## EVT-003 — Multiple Touch

Price touches the same level again after a previous touch.

---

## EVT-004 — Break

### Definition

Price closes beyond a level.

### Rule

Bullish Break

```
Close > Level
```

Bearish Break

```
Close < Level
```

---

## EVT-005 — Rejection

Price touches a level but fails to close beyond it.

The candle closes back on the original side of the level.

---

## EVT-006 — Retest

Price revisits a previously broken level.

Retest must occur after a confirmed break.

---

## EVT-007 — Acceptance

Price remains beyond a broken level for a predefined confirmation period.

Acceptance confirms that the level has changed role.

---

## EVT-008 — Failure

Price breaks a level but immediately reverses back.

Failure invalidates the breakout.

---

## EVT-009 — Bounce

Price touches a level and immediately moves away without breaking it.

---

## EVT-010 — Continuation

Price continues moving in the direction of the previous confirmed break.

---

## EVT-011 — Reversal

Price changes direction after interacting with a level.

---

## EVT-012 — Magnet

Price repeatedly returns toward a specific level before choosing direction.

---

## EVT-013 — Gap Cross

Opening gap starts beyond a level.

The level is crossed without intraday interaction.

---

## EVT-014 — Target Hit

Price reaches the next expected ORB level.

Examples

ORB High → R1

R1 → R2

ORB Low → S1

---

## EVT-015 — End of Session

Final event recorded before market close.

Used to terminate the event sequence.

---

# 6. Event Object

Each detected event contains:

| Field | Description |
|--------|-------------|
| event_id | Unique identifier |
| timestamp | Event time |
| event_type | Event classification |
| level_name | Related ORB level |
| direction | Bullish / Bearish |
| price | Event price |
| candle_index | Candle number |
| metadata | Additional information |

---

# 7. Event Sequence

Individual events are ordered chronologically.

Example

```
09:35 First Touch ORB High

↓

09:40 Break ORB High

↓

09:55 Retest ORB High

↓

10:10 Acceptance

↓

10:40 Target Hit R1

↓

11:05 Target Hit R2
```

Research operates primarily on these sequences rather than raw candles.

---

# 8. Event Quality Rules

Every detected event must satisfy:

- Deterministic definition
- Single timestamp
- Associated level
- Associated candle
- No duplicate event IDs
- Chronological ordering

---

# 9. Future Events

Future versions may introduce:

- Liquidity Sweep
- False Break
- Compression
- Expansion
- Momentum Spike
- Volatility Burst

These must be added without changing existing definitions.

---

# 10. Conclusion

The Event Dictionary defines the canonical language used by the ORB Behavior Atlas.

All research, behavior discovery, validation, and strategy generation depend on these standardized event definitions.
