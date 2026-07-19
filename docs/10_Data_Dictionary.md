# Data Dictionary

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines every data object and field used within the ORB Behavior Atlas.

It serves as the single source of truth for field names, data types, and meanings.

Every Python model, database table, report, and research module must follow these definitions.

---

# 2. Naming Standards

## General Rules

- Use `snake_case`
- Use lowercase only
- Use descriptive names
- Never abbreviate unless universally understood
- Use consistent naming across the entire project

Example:

```
orb_high
orb_low
orb_mid
trading_date
event_type
```

---

# 3. Session Object

| Field | Type | Description |
|---------|------|-------------|
| session_date | Date | Trading session date |
| instrument | Instrument | Instrument name |
| timeframe | Timeframe | Candle timeframe |
| weekday | Weekday | Day of week |
| is_weekly_expiry | Boolean or None | Weekly expiry: confirmed true, confirmed false, or unknown |
| is_monthly_expiry | Boolean or None | Monthly expiry: confirmed true, confirmed false, or unknown |
| has_holiday_gap | Boolean or None | Holiday gap: confirmed true, confirmed false, or unknown |
| candles | Tuple[Candle, ...] | Canonical candles in supplied strictly increasing timestamp order |

Session metadata is never inferred during session construction. `None` is the
canonical representation of an undetermined metadata fact.

---

# 4. Candle Object

| Field | Type | Description |
|---------|------|-------------|
| instrument | Instrument | Instrument name |
| timeframe | Timeframe | Candle timeframe |
| timestamp | Datetime | Candle timestamp |
| session_date | Date | Trading session date |
| open | Float | Opening price |
| high | Float | Highest price |
| low | Float | Lowest price |
| close | Float | Closing price |
| volume | Integer | Trading volume |

For canonical candles, `session_date` is derived from the candle timestamp
after it has been normalized to the `Asia/Kolkata` trading-session timezone.

## Storage Identity

| Object | Identity Fields | Description |
|---------|-----------------|-------------|
| Candle | instrument, timeframe, timestamp | Canonical candle storage identity |
| Session | session_date, instrument, timeframe | Canonical session storage identity |

Storage identity never includes provider-native identifiers. Candle
`session_date` is derived metadata and is not part of candle identity.

## Quality Assessment

| Field | Type | Description |
|---------|------|-------------|
| code | QualityCode | Stable observational quality category |
| severity | QualitySeverity | Informational, warning, or error classification |
| previous_timestamp | Datetime | Earlier canonical timestamp in an interval observation |
| current_timestamp | Datetime | Later canonical timestamp in an interval observation |
| expected_interval | Timedelta | Canonical interval derived from Timeframe |
| observed_interval | Timedelta | Observed immutable timestamp interval |

Quality findings are observational. They do not diagnose the cause of an
irregular interval or modify canonical data.

---

# 5. OpeningRange Object

| Field | Type | Description |
|---------|------|-------------|
| window | ORBWindow | Start-inclusive, end-exclusive canonical timestamp window |
| open | Float | Opening price of the first included candle |
| high | Float | Highest observed price among included candles |
| low | Float | Lowest observed price among included candles |
| close | Float | Closing price of the final included candle |
| candles | Tuple[Candle, ...] | Exact canonical candles included in the range |

`OpeningRange` is an immutable observed-fact record. Derived ORB values and
levels are not part of M4.2.

## ORBEscapeEvent Object

| Field | Type | Description |
|---------|------|-------------|
| timestamp | Datetime | Canonical timestamp of the escape candle |
| direction | ORBEscapeDirection | `UPWARD` or `DOWNWARD` crossed boundary |
| candle | Candle | Canonical candle containing the observed escape |
| boundary_crossed | Float | Opening-range high or low crossed by the candle |
| crossing_price | Float | Candle high for upward, or low for downward, escape |

An `ORBEscapeEvent` records only the first post-range boundary exit. It does
not confirm a breakout or classify the market response.

## ORBPostEscapeObservation Object

| Field | Type | Description |
|---------|------|-------------|
| highest_price | Float or None | Highest candle high strictly after escape |
| lowest_price | Float or None | Lowest candle low strictly after escape |
| maximum_favorable_excursion | Float or None | Non-negative distance from crossed boundary in escape direction |
| maximum_adverse_excursion | Float or None | Non-negative distance from crossed boundary opposite escape direction |
| returned_inside_range | Boolean | Whether a later candle price interval intersects the opening range |
| first_return_inside_timestamp | Datetime or None | First later timestamp whose candle interval intersects range |

When no candles follow the escape, extrema and excursions are `None`. This
record describes only observed facts; it does not classify the escape outcome.

## ORBBehavior Object

| Field | Type | Description |
|---------|------|-------------|
| kind | ORBBehaviorKind | `NO_ESCAPE`, `ESCAPE_WITH_RETURN`, or `ESCAPE_WITHOUT_RETURN` |

`ORBBehavior` is a pure classification of supplied observations. It contains no
recalculated market values or outcome inference.

---

# 6. ORB Levels

| Field | Type | Description |
|---------|------|-------------|
| r1 | Float | Resistance Level 1 |
| r2 | Float | Resistance Level 2 |
| r3 | Float | Resistance Level 3 |
| r4 | Float | Resistance Level 4 |
| r5 | Float | Resistance Level 5 |
| s1 | Float | Support Level 1 |
| s2 | Float | Support Level 2 |
| s3 | Float | Support Level 3 |
| s4 | Float | Support Level 4 |
| s5 | Float | Support Level 5 |

---

# 7. Event Object

| Field | Type | Description |
|---------|------|-------------|
| event_id | Integer | Unique event identifier |
| timestamp | Datetime | Event time |
| event_type | String | Event classification |
| level_name | String | Associated ORB level |
| price | Float | Event price |
| candle_index | Integer | Candle number from market open |

---

# 8. Behavior Object

| Field | Type | Description |
|---------|------|-------------|
| behavior_name | String | Behavior identifier |
| start_time | Datetime | Behavior start |
| end_time | Datetime | Behavior end |
| confidence | Float | Confidence score |
| evidence_count | Integer | Supporting observations |

---

# 9. Research Object

| Field | Type | Description |
|---------|------|-------------|
| research_id | String | Research question ID |
| hypothesis | String | Hypothesis statement |
| sample_size | Integer | Number of observations |
| probability | Float | Measured probability |
| average_move | Float | Average price movement |
| average_duration | Float | Average duration |
| conclusion | String | Research conclusion |

---

# 10. Validation Object

| Field | Type | Description |
|---------|------|-------------|
| validation_status | String | Validation result |
| walk_forward | Boolean | Walk-forward passed |
| out_of_sample | Boolean | Out-of-sample passed |
| robustness_score | Float | Robustness rating |
| p_value | Float | Statistical significance |
| confidence_interval | Float | Confidence interval |

---

# 11. Strategy Object

| Field | Type | Description |
|---------|------|-------------|
| strategy_id | String | Strategy identifier |
| strategy_name | String | Strategy name |
| entry_rule | String | Entry logic |
| exit_rule | String | Exit logic |
| stop_rule | String | Stop-loss logic |
| target_rule | String | Target logic |
| expectancy | Float | Strategy expectancy |

---

# 12. Data Quality Rules

Every dataset must satisfy the following:

- No duplicate timestamps
- No missing OHLC values
- High ≥ Open
- High ≥ Close
- Low ≤ Open
- Low ≤ Close
- Volume ≥ 0
- Chronological order maintained

Any violation must be flagged before research begins.

Canonical candle validation returns ordered, immutable issue records for these
semantic violations. M2.5 emits only error-severity issues; warning and quality
aggregation semantics are reserved for later milestones. Duplicate and ordering
checks use canonical `Candle.timestamp` values after normalization.

---

# 13. Version Control

New fields may only be added if:

- They support a research question.
- They are documented here.
- Their purpose is clearly defined.
- Existing field names are not broken.

---

# 14. Conclusion

This Data Dictionary defines the canonical data model for the ORB Behavior Atlas.

All future implementations must conform to these definitions to ensure consistency, reproducibility, and maintainability.
