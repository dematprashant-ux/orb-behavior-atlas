# Portfolio Engine

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

The Portfolio Engine manages capital across multiple validated trading strategies.

Its responsibility is to transform individual strategy outputs into a coherent portfolio while enforcing portfolio-level risk controls, capital allocation policies, and exposure limits.

The Portfolio Engine manages portfolios.

It does not create strategies.

---

# 2. Responsibilities

The Portfolio Engine is responsible for:

- Capital allocation
- Strategy allocation
- Portfolio construction
- Position aggregation
- Portfolio risk management
- Exposure monitoring
- Rebalancing
- Performance attribution
- Portfolio reporting

---

# 3. Inputs

The Portfolio Engine accepts:

- Approved Strategy Objects
- Portfolio Configuration
- Capital Configuration
- Risk Configuration
- Market Data
- Current Positions

Only approved strategies may be included.

---

# 4. Portfolio Workflow

```
Approved Strategies

↓

Capital Allocation

↓

Position Allocation

↓

Risk Checks

↓

Portfolio Construction

↓

Performance Monitoring

↓

Portfolio Report
```

---

# 5. Portfolio Structure

A portfolio consists of:

- Portfolio
    - Strategies
        - Positions
            - Orders
                - Trades

Each object has an independent lifecycle.

---

# 6. Capital Allocation

Capital allocation determines how portfolio capital is distributed.

Supported allocation methods:

- Fixed allocation
- Equal allocation
- Percentage allocation
- Volatility-adjusted allocation
- Risk-budget allocation

Future allocation methods may be added without changing interfaces.

---

# 7. Strategy Allocation

Each strategy receives:

- Allocation percentage
- Maximum capital
- Maximum leverage
- Risk budget
- Trading permissions

Allocation must be deterministic and reproducible.

---

# 8. Position Aggregation

The engine combines positions across all active strategies.

For each position track:

- Strategy ID
- Instrument
- Direction
- Quantity
- Entry Price
- Current Value
- Unrealized PnL
- Realized PnL
- Portfolio Weight

---

# 9. Portfolio Risk Management

Portfolio-level controls include:

- Maximum portfolio drawdown
- Maximum daily loss
- Maximum position size
- Maximum leverage
- Maximum simultaneous positions
- Concentration limits
- Sector or instrument limits (future)

Risk rules override individual strategy rules when necessary.

---

# 10. Exposure Management

Monitor:

- Gross Exposure
- Net Exposure
- Long Exposure
- Short Exposure
- Cash Allocation
- Capital Utilization

Exposure metrics should update after every portfolio event.

---

# 11. Correlation Management

The engine should support:

- Strategy correlation
- Instrument correlation
- Exposure overlap
- Risk concentration

Future versions may dynamically reduce allocation based on excessive correlation.

---

# 12. Rebalancing

Supported approaches:

- Periodic
- Threshold-based
- Risk-triggered
- Manual

Rebalancing must preserve complete audit history.

---

# 13. Portfolio Object

Each portfolio contains:

| Field | Description |
|--------|-------------|
| portfolio_id | Permanent identifier |
| portfolio_name | Portfolio name |
| capital | Initial capital |
| available_cash | Current cash |
| invested_capital | Allocated capital |
| active_strategies | Strategy references |
| active_positions | Position references |
| exposure | Exposure summary |
| risk_metrics | Portfolio risk |
| performance | Portfolio statistics |
| status | Active / Paused / Closed |

Portfolio objects remain version controlled.

---

# 14. Performance Metrics

Track:

- Portfolio Return
- CAGR
- Volatility
- Maximum Drawdown
- Sharpe Ratio
- Sortino Ratio
- Calmar Ratio
- Profit Factor
- Recovery Factor
- Win Rate
- Rolling Performance
- Strategy Attribution

Performance should be attributable to individual strategies.

---

# 15. Public Interfaces

The Portfolio Engine should expose functions equivalent to:

```
build_portfolio()

allocate_capital()

rebalance()

get_portfolio()

get_exposure()

get_performance()

export_portfolio()
```

Interfaces should remain stable.

---

# 16. Error Handling

The engine should detect and report:

- Missing strategies
- Invalid allocations
- Capital inconsistencies
- Negative balances
- Exposure violations
- Duplicate portfolio IDs
- Invalid risk configuration

Errors must include sufficient diagnostic information.

---

# 17. Performance Goals

The Portfolio Engine should provide:

- Deterministic allocation
- Efficient portfolio updates
- Real-time exposure calculation
- Low memory overhead
- Scalable multi-strategy support

Performance improvements must never compromise accounting accuracy.

---

# 18. Dependencies

Depends on:

- Strategy Engine
- Backtesting Framework
- Validation Engine

Provides outputs to:

- Live Execution Engine
- Monitoring System
- Project Dashboard

---

# 19. Design Principles

The Portfolio Engine must always be:

- Deterministic
- Reproducible
- Auditable
- Risk-first
- Strategy-independent
- Fully version controlled

Portfolio risk always has priority over individual strategy objectives.

---

# 20. Future Enhancements

Future versions may include:

- Dynamic capital allocation
- Regime-aware portfolio switching
- Risk parity allocation
- Kelly optimization
- Cross-asset portfolios
- Multi-broker support
- Live portfolio synchronization
- AI-assisted allocation optimization

---

# 21. Conclusion

The Portfolio Engine provides portfolio-level management for the ORB Behavior Atlas by coordinating validated strategies under a unified capital allocation and risk management framework.

It ensures that multiple strategies operate together in a controlled, measurable, and reproducible manner while maintaining strict portfolio-level risk discipline.
