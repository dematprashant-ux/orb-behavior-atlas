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

## 1.1 Portfolio Domain Foundation

M16.1 establishes the immutable portfolio-domain boundary. A
`PortfolioPosition` records an active holding's stable position identity,
canonical instrument, side, quantity, explicit entry price, and aware entry
timestamp. A `PortfolioSnapshot` records available cash plus an ordered tuple
of unique active positions at one aware timestamp.

Snapshots expose entry-based invested capital only; they do not imply a market
valuation, unrealized PnL, an exit state, lifecycle transition, allocation, or
portfolio analytics. Empty snapshots are valid. Construction retains supplied
immutable position references and does not mutate caller collections.

## 1.2 Capital Allocation Foundation

M16.2 keeps capital-allocation decisions separate from portfolio state changes.
An immutable `AllocationRequest` contains available cash only, and an
immutable `AllocationDecision` contains allocated capital only. The
`CapitalAllocationPolicy` protocol is stateless and deterministic. Its fixed
policy caps configured capital at available cash; its percentage policy uses
available cash as its explicit and only capital base.

Allocation does not size orders, open or close positions, alter cash, access
market data, calculate costs, or use global configuration. A zero-capital
decision is a valid deterministic allocation fact; later lifecycle code owns
the decision whether it can create a position.

## 1.3 Multi-Position Portfolio Engine

M16.3 adds `StandardPortfolioEngine`, which applies caller-supplied
`PortfolioOpenEvent` and `PortfolioCloseEvent` values in their exact supplied
order. It begins with an immutable snapshot and returns that snapshot followed
by a new immutable snapshot for every accepted event. Equal timestamps retain
their input order; decreasing event timestamps are rejected.

On an open, the injected allocation policy supplies a capital cap. The engine
uses whole integer units, matching the existing `CompletedTrade` quantity
contract, deducts actual entry capital, and leaves any non-purchasable
remainder as cash. On close, it removes the active position and restores
`quantity * exit_price` exactly once. The engine neither recomputes transaction
costs nor performs valuation, analytics, reporting, retries, or I/O.

## 1.4 Portfolio Equity Curve

M16.4 builds portfolio equity from immutable snapshots through an explicit
injected valuation policy. Each `PortfolioEquityPoint` contains a snapshot's
timestamp, cash, active-position value, and exact total equity (`cash +
position_value`). `PortfolioEquityCurve` retains the resulting points in the
caller-supplied snapshot order.

`CostBasisPortfolioValuation` is the deterministic baseline and values active
positions only from their explicit entry capital. It does not claim market
valuation or unrealized PnL. Other policies own any explicit valuation facts.
Closed positions contribute only through snapshot cash, so entry capital is
not double counted. The boundary accesses no market data, recalculates no
transaction costs, and produces no performance, drawdown, or reporting data.

## 1.5 Portfolio Performance Metrics

M16.5 derives immutable performance facts only from `PortfolioEquityCurve`.
`PortfolioPerformanceMetrics` records initial and final equity, absolute and
total return, equity extrema, and point count. Absolute return is `final -
initial`; total return is `absolute_return / initial`. Empty curves have zero
equity facts and an unavailable (`None`) total return, avoiding invented
infinities. Single-point curves have zero absolute and total return when their
initial equity is non-zero.

Portfolio metrics do not inspect positions, value holdings, calculate costs,
or recreate trade statistics. Portfolio drawdown has a separate result model
but reuses the existing shared absolute-drawdown mathematics; it is calculated
from the same portfolio equity curve and retains source equity-point references.

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
