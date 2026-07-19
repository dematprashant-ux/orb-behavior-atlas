# Event Engine

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

The Event Engine transforms raw market data into standardized market events.

Its responsibility is to continuously observe price interaction with the 13 ORB-derived levels and convert those interactions into deterministic, timestamped events.

The Event Engine is the first layer of market interpretation.

---

# 2. Responsibilities

The Event Engine is responsible for:

- Monitoring every candle
- Monitoring every ORB level
- Detecting market events
- Maintaining chronological event order
- Preventing duplicate events
- Producing immutable event objects
- Providing events to downstream engines

---

# 3. Inputs

The Event Engine requires:

- Validated candles (Data Engine)
- ORB Object (ORB Engine)
- ORB Levels

Inputs must already be validated.

---

# 4. Event Detection Pipeline

```
Candles

↓

ORB Levels

↓

Price Interaction

↓

Rule Evaluation

↓

Event Detection

↓

Event Validation

↓

Event Object

↓

Event Stream
```

---

# 5. Supported Events

Version 1.0 supports:

- Touch
- First Touch
- Multiple Touch
- Break
- Rejection
- Retest
- Acceptance
- Failure
- Bounce
- Continuation
- Reversal
- Magnet
- Gap Cross
- Target Hit
- End of Session

Definitions are maintained in the Event Dictionary.

---

# 6. Event Priority

When multiple events occur on the same candle, priority determines recording order.

Highest priority first:

1. Gap Cross
2. Break
3. Failure
4. Acceptance
5. Rejection
6. Retest
7. Bounce
8. Continuation
9. Reversal
10. Touch
11. Multiple Touch
12. Target Hit
13. End of Session

Only valid event combinations may coexist.

---

# 7. Event Sequencing

Events are stored chronologically.

Example

```
09:35 First Touch ORB High

↓

09:40 Break

↓

09:45 Retest

↓

09:50 Acceptance

↓

10:20 Target Hit R1
```

Sequences are immutable after creation.

---

# 8. Event State Machine

Each ORB level maintains an independent state.

```
Untouched

↓

Touched

↓

Broken

↓

Retested

↓

Accepted

↓

Completed
```

Failure or rejection may transition a level back to an earlier state where appropriate.

---

# 9. Multi-Level Interactions

A single candle may interact with multiple ORB levels.

The engine must:

- Detect every valid interaction
- Preserve chronological ordering
- Prevent duplicate events
- Associate every event with exactly one level

---

# 10. Event Object

Every event contains:

| Field | Description |
|--------|-------------|
| event_id | Permanent identifier |
| session_date | Trading day |
| timestamp | Event time |
| candle_index | Candle number |
| event_type | Event classification |
| level_name | ORB level |
| price | Trigger price |
| direction | Bullish / Bearish / Neutral |
| confidence | Detection confidence |
| metadata | Additional information |

Event objects are immutable.

---

# 11. Validation Rules

Every event must satisfy:

- Valid timestamp
- Valid ORB level
- Valid event type
- Unique event ID
- Correct sequence
- No duplicate detection
- Supported state transition

Invalid events are discarded and logged.

---

# 12. Public Interfaces

The Event Engine should expose functions equivalent to:

```
detect_events()

get_events()

get_events_by_level()

get_events_by_type()

validate_events()

export_events()
```

Interfaces should remain stable across versions.

---

# 13. Error Handling

The engine should detect and report:

- Missing ORB object
- Missing candle data
- Invalid level references
- Invalid timestamps
- Duplicate events
- Invalid state transitions

Errors should include sufficient context for debugging.

---

# 14. Performance Goals

The Event Engine should provide:

- Deterministic detection
- Chronological consistency
- Constant-time event lookup
- Minimal memory usage
- Reproducible outputs

---

# 15. Dependencies

Depends on:

- Data Engine
- ORB Engine

Provides data to:

- Behavior Engine
- Research Engine
- Validation Engine
- Strategy Engine

---

# 16. Future Enhancements

Future versions may include:

- Liquidity Sweep detection
- False Break detection
- Volume-confirmed events
- Multi-timeframe event detection
- Event confidence calibration
- Live streaming support
- Event clustering

---

# 17. Design Principles

The Event Engine must always be:

- Deterministic
- Stateless between sessions
- Fully reproducible
- Independent of strategy logic
- Independent of optimization
- Auditable

It is responsible only for identifying market events, not interpreting them.

---

# 18. Conclusion

The Event Engine converts standardized ORB price interactions into a chronological stream of validated events. These events form the canonical language used by the Behavior Engine, Research Engine, and all downstream components of the ORB Behavior Atlas.
