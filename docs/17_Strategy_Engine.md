# Strategy Engine

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

The Strategy Engine converts validated market edges into executable trading strategies.

It is the only component responsible for creating trading rules. Every strategy must originate exclusively from validated evidence produced by the Validation Engine.

The Strategy Engine never creates research or validates hypotheses.

## 1.1 Strategy Engine Foundation

M8.1 establishes the technology-neutral Strategy Engine boundary. It exposes
immutable `StrategyContext` and `StrategyDecision` models, stable structural
`StrategyDecisionType` values, and the pure `Strategy` protocol. A context
references one completed `ORBBehaviorRecord` within its existing
`ORBBehaviorAtlas`; it does not copy child research values.

This foundation defines no decision rules. It does not generate signals,
execute trades, size positions, calculate PnL, backtest, inspect candles, or
perform I/O.

## 1.2 Rule-Based ORB Strategy

M8.2 adds `ORBRuleStrategy`, a deterministic non-executing implementation of
the `Strategy` protocol. It maps only existing behavior facts: `NO_ESCAPE` and
`ESCAPE_WITH_RETURN` map to `NO_ACTION`; `ESCAPE_WITHOUT_RETURN` maps its
existing upward or downward escape direction to `LONG_SETUP` or `SHORT_SETUP`.

It does not inspect candles, recalculate research facts, generate features,
execute trades, manage positions, calculate PnL, or backtest. Its structural
setup results do not authorize an executable trading strategy.

---

# 2. Responsibilities

The Strategy Engine is responsible for:

- Building strategies from validated edges
- Combining compatible edges
- Defining entry rules
- Defining exit rules
- Applying risk management
- Position sizing
- Strategy versioning
- Strategy evaluation
- Producing immutable strategy objects

---

# 3. Inputs

The Strategy Engine accepts:

- Validated Edges
- Validation Reports
- ORB Objects
- Behavior Objects
- Event Objects
- Strategy Configuration

All inputs must originate from validated upstream components.

M8.1 and M8.2 are non-executable structural exceptions: they reference
completed research records and their atlas without authorizing an executable
strategy. Future concrete production strategies remain restricted to validated
upstream evidence.

---

# 4. Strategy Generation Workflow

```
Validated Edge

↓

Edge Selection

↓

Rule Composition

↓

Entry Rules

↓

Exit Rules

↓

Risk Rules

↓

Position Sizing

↓

Strategy Object

↓

Backtesting
```

---

# 5. Strategy Design Principles

Every strategy must be:

- Evidence-driven
- Deterministic
- Reproducible
- Explainable
- Version controlled
- Independently testable

Strategies must never contain discretionary rules.

---

# 6. Edge Selection

Only edges with production approval may be used.

Selection criteria may include:

- Confidence Score
- Evidence Score
- Regime compatibility
- Stability
- Recent monitoring status

Experimental or rejected edges are prohibited.

---

# 7. Rule Composition

A strategy consists of modular rules.

Core rule groups:

- Entry Rules
- Exit Rules
- Risk Rules
- Position Rules
- Session Rules
- Portfolio Rules

Each rule should remain independently configurable.

---

# 8. Entry Rules

Entry rules specify when a trade becomes eligible.

Typical components:

- Required behavior
- Required event sequence
- ORB level interaction
- Direction
- Time constraints
- Confirmation requirements

Entry rules must reference validated edges.

---

# 9. Exit Rules

Exit rules define how positions are closed.

Examples:

- Target reached
- Stop-loss triggered
- Time-based exit
- End-of-session exit
- Opposite validated signal
- Edge invalidation

Multiple exit conditions may coexist.

---

# 10. Risk Management

Every strategy must define:

- Maximum risk per trade
- Maximum daily risk
- Maximum open positions
- Maximum drawdown threshold
- Session loss limit

Risk rules remain independent of entry logic.

---

# 11. Position Sizing

The Strategy Engine determines position sizing using configurable methods.

Possible approaches:

- Fixed quantity
- Fixed capital
- Fixed percentage risk
- Volatility-adjusted sizing
- Kelly-based sizing (future)

Sizing logic must be deterministic.

---

# 12. Strategy Object

Each strategy produces one immutable Strategy Object.

| Field | Description |
|--------|-------------|
| strategy_id | Permanent identifier |
| strategy_name | Strategy name |
| version | Strategy version |
| related_edges | Source edges |
| entry_rules | Entry definition |
| exit_rules | Exit definition |
| risk_rules | Risk configuration |
| position_rules | Position sizing |
| created_date | Creation date |
| status | Draft / Tested / Approved / Retired |
| metadata | Additional information |

---

# 13. Backtesting Interface

The Strategy Engine provides strategies to the backtesting framework.

Expected outputs include:

- Trade list
- Equity curve
- Performance metrics
- Drawdown profile
- Risk statistics
- Strategy diagnostics

Backtesting implementation remains external to the engine.

---

# 14. Public Interfaces

The Strategy Engine should expose functions equivalent to:

```
build_strategy()

get_strategy()

list_strategies()

evaluate_strategy()

export_strategy()

retire_strategy()
```

Interfaces should remain stable across versions.

---

# 15. Validation Requirements

Before approval, every strategy must:

- Use only validated edges
- Produce deterministic outputs
- Pass backtesting
- Pass walk-forward testing
- Meet predefined performance criteria

Strategies failing validation remain in Draft or Tested status.

---

# 16. Error Handling

The engine should detect and report:

- Missing edge references
- Invalid rule definitions
- Conflicting rules
- Unsupported configurations
- Duplicate strategy IDs
- Invalid risk parameters

Errors must include sufficient diagnostic information.

---

# 17. Performance Goals

The Strategy Engine should provide:

- Deterministic rule generation
- Fast strategy construction
- Stable interfaces
- Reproducible outputs
- Efficient evaluation support

Performance optimizations must not alter strategy logic.

---

# 18. Dependencies

Depends on:

- Validation Engine
- Edge Repository
- ORB Engine
- Event Engine
- Behavior Engine

Provides outputs to:

- Backtesting Framework
- Portfolio Engine
- Live Execution Engine (future)
- Project Dashboard

---

# 19. Design Principles

The Strategy Engine must always be:

- Evidence-driven
- Modular
- Explainable
- Reproducible
- Auditable
- Independent of research generation

Research discovers edges.

Validation approves edges.

The Strategy Engine converts approved edges into executable trading systems.

---

# 20. Future Enhancements

Future versions may include:

- Automatic strategy generation
- Multi-edge optimization
- Portfolio construction
- Regime-aware strategy switching
- Adaptive position sizing
- Reinforcement learning integration
- Live execution support
- Continuous strategy monitoring

---

# 21. Conclusion

The Strategy Engine is the production layer of the ORB Behavior Atlas.

It transforms validated market knowledge into executable trading strategies while preserving the project's core philosophy: every trading decision must be traceable to statistically validated evidence, ensuring a clear separation between research, validation, and execution.
