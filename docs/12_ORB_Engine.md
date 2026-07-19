# ORB Engine

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

The ORB Engine constructs the Opening Range Breakout (ORB) structure for every trading session.

It transforms validated intraday market data into a standardized ORB object that serves as the foundation for event detection, behavior discovery, statistical research, validation, and strategy generation.

---

# 2. Responsibilities

The ORB Engine is responsible for:

- Identifying the Opening Range
- Calculating ORB High
- Calculating ORB Low
- Calculating ORB Mid
- Generating R1–R5 levels
- Generating S1–S5 levels
- Validating ORB calculations
- Creating immutable ORB objects
- Providing ORB data to downstream engines

---

# 3. Inputs

The ORB Engine accepts:

- Validated intraday candles
- Trading session information
- ORB configuration

Inputs must originate from the Data Engine.

---

# 4. ORB Configuration

Version 1.0 default configuration:

| Parameter | Value |
|-----------|------|
| Session Start | 09:15 IST |
| ORB Start | 09:15 IST |
| ORB End | 09:30 IST |
| ORB Duration | 15 Minutes |

Future versions may support configurable ORB windows.

---

# 5. ORB Construction

The Opening Range consists of all candles between:

```
09:15:00 IST

↓

09:29:59 IST
```

For a 5-minute timeframe this normally includes:

- 09:15 candle
- 09:20 candle
- 09:25 candle

---

# 6. ORB Calculations

### ORB High

Highest High inside the ORB window.

```
ORB High = MAX(High)
```

---

### ORB Low

Lowest Low inside the ORB window.

```
ORB Low = MIN(Low)
```

---

### ORB Range

```
ORB Range = ORB High − ORB Low
```

---

### ORB Mid

```
ORB Mid = (ORB High + ORB Low) / 2
```

---

# 7. Level Generation

The ORB Range is projected above and below the Opening Range.

Resistance Levels

```
R1 = ORB High + 1 × ORB Range
R2 = ORB High + 2 × ORB Range
R3 = ORB High + 3 × ORB Range
R4 = ORB High + 4 × ORB Range
R5 = ORB High + 5 × ORB Range
```

Support Levels

```
S1 = ORB Low − 1 × ORB Range
S2 = ORB Low − 2 × ORB Range
S3 = ORB Low − 3 × ORB Range
S4 = ORB Low − 4 × ORB Range
S5 = ORB Low − 5 × ORB Range
```

---

# 8. Canonical Level Order

Every trading day must expose levels in the following order:

```
S5
S4
S3
S2
S1
ORB Low
ORB Mid
ORB High
R1
R2
R3
R4
R5
```

This ordering is fixed throughout the project.

---

# 9. ORB Object

Every session produces exactly one ORB object.

| Field | Description |
|--------|-------------|
| session_date | Trading date |
| orb_start | Start timestamp |
| orb_end | End timestamp |
| orb_high | Opening range high |
| orb_low | Opening range low |
| orb_mid | Midpoint |
| orb_range | High − Low |
| R1–R5 | Resistance levels |
| S1–S5 | Support levels |
| source_timeframe | Source timeframe |
| status | Valid / Invalid |

---

# 10. Validation Rules

The ORB object is valid only if:

- ORB High > ORB Low
- ORB Range > 0
- ORB Mid lies between High and Low
- All ORB candles are present
- No duplicate timestamps exist
- Session data passed Data Engine validation

Invalid ORB objects must not be passed to downstream engines.

---

# 11. Public Interfaces

The ORB Engine should expose functions equivalent to:

```
build_orb()

get_orb()

get_level(level_name)

get_all_levels()

validate_orb()

export_orb()
```

Public interfaces should remain stable across versions.

---

# 12. Error Handling

The engine should detect and report:

- Missing ORB candles
- Incomplete ORB window
- Zero ORB range
- Invalid timestamps
- Invalid session
- Duplicate candles

Errors should be logged with sufficient detail for debugging.

---

# 13. Performance Goals

The ORB Engine should provide:

- Deterministic calculations
- One ORB object per session
- Constant-time level lookup
- Minimal memory overhead
- Reproducible outputs

---

# 14. Dependencies

The ORB Engine depends on:

- Data Engine

The following engines depend on the ORB Engine:

- Event Engine
- Behavior Engine
- Research Engine
- Validation Engine
- Strategy Engine

---

# 15. Future Enhancements

Future versions may include:

- Configurable ORB durations
- Multiple ORB windows
- ATR-scaled projection levels
- Volume-weighted ORB
- Multi-timeframe ORB
- Alternative projection models
- Live ORB updates

---

# 16. Conclusion

The ORB Engine creates the canonical Opening Range representation for every trading session.

By producing a validated and standardized ORB object with fixed support and resistance levels, it establishes the reference framework used throughout the ORB Behavior Atlas for all subsequent event detection, behavioral analysis, and quantitative research.
