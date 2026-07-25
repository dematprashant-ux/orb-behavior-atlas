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

## 1.3 Parameter Space Domain

M18.1 adds immutable `DiscreteParameter`, `ParameterSpace`, and
`CandidateParameterSet` values to describe finite candidate strategy
parameters. Values are explicit ordered scalar or enum-backed alternatives;
the domain rejects blank names, mutable collections, duplicate values, and
mixed parameter value types. It defines no strategy configuration, search,
optimization, training, scoring, ranking, execution, serialization, or I/O.

## 1.4 Deterministic Grid Candidate Generation

M18.2 adds the pure `CandidateGenerator` protocol and
`GridCandidateGenerator`. It enumerates the finite Cartesian product of an
existing `ParameterSpace` into ordered immutable `CandidateParameterSet`
values. Parameter declaration order and each parameter's candidate-value order
are retained; the final parameter changes fastest. The generator does not
evaluate, score, rank, train, execute, optimize, report, serialize, or perform
I/O.

## 1.5 Candidate Evaluation Contracts

M18.3 adds the protocol-only `CandidateEvaluator` contract and immutable
`CandidateEvaluation` hand-off. An evaluator receives one existing
`CandidateParameterSet` and returns an existing immutable `BacktestRun` by
reference as its outcome. This keeps candidate generation independent from
evaluation while avoiding duplicate backtest or performance result models.

The contract defines no evaluator implementation, grid-search runner, random
search, Bayesian search, optimization loop, ranking, scoring algorithm,
walk-forward integration, reporting, serialization, or I/O. Future search
approaches can reuse the same candidate-evaluation boundary without changing
candidate generation.

## 1.6 Deterministic Grid Search Runner

M18.4 adds `GridSearchRunner`, `StandardGridSearchRunner`, and immutable
`GridSearchRun`. The standard runner receives injected `CandidateGenerator`
and `CandidateEvaluator` collaborators, generates candidates once from one
existing `ParameterSpace`, then evaluates each candidate sequentially in the
generator's exact order. The run retains the source parameter space and its
ordered `CandidateEvaluation` values without copying, sorting, or selecting
them.

This runner performs orchestration only. It defines no score, ranking metric,
winner selection, optimizer heuristic, random behavior, walk-forward work,
reporting, serialization, I/O, or concurrency. Future random-search and
Bayesian-search runners can reuse the same evaluation contract while defining
their own candidate-generation policies.

## 1.7 Objective and Scoring Contracts

M18.5 adds the protocol-only `CandidateObjective` boundary and immutable
`ObjectiveScore`. An injected objective converts an existing
`CandidateEvaluation` into one finite scalar `float` with an explicit
`ObjectiveDirection`: `maximize` or `minimize`. The score retains the source
evaluation by reference; finite integer inputs are normalized to the same
canonical `float` representation used by existing performance metrics. It
introduces neither a new performance calculation nor an untyped objective
identifier.

This milestone does not rank, select, normalize, weight, compare, or otherwise
optimize candidates. It adds no concrete objective formula, search-loop change,
walk-forward integration, reporting, serialization, I/O, or concurrency.
Future selection policies can consume these typed scores without changing
candidate generation or evaluation contracts.

## 1.8 Deterministic Objective Ranking

M18.6 adds `ObjectiveRanker`, `StandardObjectiveRanker`, immutable
`ObjectiveRanking`, and `RankedObjectiveScore`. The standard ranker is created
with an explicit `ObjectiveDirection`, which makes empty rankings well-defined
without an implicit default. It orders matching `ObjectiveScore` values by their
existing scalar score: descending for `maximize` and ascending for `minimize`.
Equal scores preserve their supplied order; ranks are one-based positions in
that final stable order.

Ranking creates no score, winner, top-k subset, threshold subset, aggregate
statistic, multi-objective rule, or search behavior. It does not alter grid
search, integrate walk-forward execution, render, serialize, perform I/O, or
use concurrency. Future selection policies may consume the complete immutable
ranking explicitly.

## 1.9 Deterministic Selection Policies

M18.7 adds immutable `ObjectiveSelection` with protocol-only `SelectionPolicy`
abstractions. `BestRankSelectionPolicy` selects every entry tied at the leading
score of an existing `ObjectiveRanking`; `TopRankedSelectionPolicy` selects a
supplied positive count of leading entries without expanding a cutoff tie. Both
return source-owned entries in their existing ranking order. Empty rankings
produce valid empty selections.

Selection is deliberately separate from ranking: it performs no score
calculation, comparison, reranking, winner metadata, threshold filter,
multi-objective rule, or search orchestration. It does not add random or
Bayesian search, walk-forward execution, reporting, serialization, I/O, or
concurrency.

## 1.10 Deterministic Optimization Pipeline

M18.8 adds `OptimizationRunner`, `StandardOptimizationRunner`, and immutable
`OptimizationRun`. The standard runner receives injected grid-search, scoring,
ranking, and selection collaborators. It delegates once in that order for one
existing `ParameterSpace`, retaining the resulting `GridSearchRun`, evaluation-
ordered `ObjectiveScore` tuple, `ObjectiveRanking`, and `ObjectiveSelection`.
Cross-stage references are validated without recalculating any result.

The pipeline adds no search algorithm, objective formula, ranking algorithm,
selection policy, cache, retry, random behavior, walk-forward work, report,
serialization, I/O, or concurrency. It only composes the existing deterministic
boundaries for future optimization use.

## 1.11 Explicit Optimization Configuration

M19.1 adds immutable `OptimizationConfiguration`, which owns the explicit
`ObjectiveDirection` and injected `SelectionPolicy` for one deterministic
optimization pipeline. It retains the exact policy object and contains no
runner, objective, ranker, evaluation, result, runtime state, or implicit
default. Execution collaborators remain separately constructor-injected into
`StandardOptimizationRunner`.

The configuration is the sole pipeline source for direction and selection:
every produced score must match its direction, the resulting ranking must use
it, and the configured policy receives that exact ranking. This makes empty
grid-search runs well-defined without fabricating a score: the configuration
supplies their explicit ranking direction, while the objective is not invoked.
The search, scoring, ranking, and selection sequence is otherwise unchanged.

## 1.12 Optimization Specification

M19.2 adds immutable `OptimizationSpecification`, which defines one experiment
by retaining the exact existing `ParameterSpace` and
`OptimizationConfiguration`. The parameter space describes the finite candidate
values, while the configuration remains the sole source of objective direction
and selection policy. The specification holds no execution collaborator,
runtime state, result, timestamp, statistic, or report metadata.

`OptimizationRunner.run()` now receives the specification rather than a bare
parameter space. `StandardOptimizationRunner` remains responsible only for how
the supplied experiment executes: its grid-search, objective, and ranker
collaborators remain constructor-injected. Empty runs retain their explicit
direction through the specification configuration; no score or default policy
is fabricated. This preserves the existing orchestration sequence while giving
future experiment descriptions one typed, immutable boundary.

## 1.13 Optimization Strategy Contract

M19.3 separates search execution from optimization orchestration through the
protocol-only `OptimizationStrategy`. A strategy receives an
`OptimizationSpecification` and returns an existing `GridSearchRun` without
scoring, ranking, selection, or result aggregation. `GridOptimizationStrategy`
is the first concrete adapter: it forwards the specification's exact
`ParameterSpace` once to an injected `GridSearchRunner` and retains its exact
result.

`StandardOptimizationRunner` now depends on `OptimizationStrategy`, while its
objective and ranker collaborators remain injected. This preserves the existing
orchestration sequence and makes later search strategies pluggable without
duplicating grid-search or optimization-pipeline behavior. No additional search
algorithm is implemented by this contract.

## 1.14 Generic Optimization Search Result

M19.4 adds immutable `OptimizationSearchRun`, the algorithm-neutral result of
an `OptimizationStrategy`. It contains only the ordered existing
`CandidateEvaluation` objects required by optimization orchestration. It does
not expose a parameter space, a grid shape, policy settings, scores, rankings,
selections, or execution metadata.

`GridSearchRun` remains the grid-search subsystem result and retains its source
parameter space. `GridOptimizationStrategy` adapts it to an
`OptimizationSearchRun` by retaining the exact evaluation objects in their
existing order. `StandardOptimizationRunner` now consumes the generic result,
then performs the unchanged scoring, direction validation, ranking, and
selection stages. This keeps grid details out of the generic strategy boundary
without introducing another optimization algorithm.

## 1.15 Optimization Strategy Metadata

M19.5 adds immutable `OptimizationStrategyMetadata`, a name-only description
of the algorithm that produced a search result. Metadata is separate from
execution: it has no collaborator, configuration, parameter space, runtime
state, statistic, or policy. `GridOptimizationStrategy` exposes immutable
`grid` metadata, and each `OptimizationSearchRun` retains that exact object.
`OptimizationRun` exposes the same object through its retained search run.

This records algorithm identity without changing candidate generation,
evaluation, scoring, ranking, selection, or optimization orchestration. Future
strategies can provide their own metadata without claiming an implementation
exists today.

## 1.16 Finite Parameter-Space Indexing and Random Sampling

M20.4 adds immutable `OptimizationBudget(maximum_evaluations)`, an explicit
deterministic execution limit owned by `OptimizationSpecification`. It is
separate from `OptimizationConfiguration`: configuration defines objective and
selection policy, while the budget caps only candidate evaluations. Grid and
random strategies preserve their established candidate order and evaluate at
most the specification budget; a larger budget simply permits every available
candidate. The budget provides no time limit, adaptive stopping, execution
state, scoring, ranking, or selection behavior.

M20.3 adds `ParameterSpaceIndexer` and its stateless
`CartesianParameterSpaceIndexer` implementation. It provides exact finite
Cartesian cardinality and zero-based mixed-radix `candidate_at()` access using
the canonical order established by `GridCandidateGenerator`: declared parameter
and value order are preserved and the final parameter varies fastest. Indexing
uses memory proportional only to the number of parameters; it does not
materialize a full Cartesian collection, evaluate candidates, or score, rank,
or select them.

`DeterministicRandomCandidateSampler` receives exactly one explicit indexer.
It samples deterministic unique positions from the immutable
`RandomOptimizationConfiguration(seed, maximum_samples)` and resolves those
positions through the indexer, preserving the existing seeded candidate order
without global random-state mutation. Sequential grid generation remains a
separate responsibility. The sampler and indexer provide finite-space reuse for
future strategies without claiming unsupported algorithms exist.

The M20.2 boundary remains: finite deterministic sampling is separate from
evaluation.
`RandomOptimizationConfiguration(seed, maximum_samples)` is immutable explicit
sampling input. `RandomCandidateSampler` only returns an ordered immutable tuple
of unique `CandidateParameterSet` values. The stateless
`DeterministicRandomCandidateSampler` uses the supplied seed without mutating
global random state, respects the maximum sample count, and naturally exhausts
the finite parameter space without materializing the full Cartesian product.

`RandomOptimizationStrategy` injects exactly one sampler and one
`CandidateEvaluator`. It invokes the sampler once, evaluates its exact
candidates once in sampled order, and retains the resulting exact evaluation
objects with immutable `random` strategy metadata in `OptimizationSearchRun`.
Sampling performs no evaluation, scoring, ranking, or selection; the strategy
does not own random-number generation. This contract permits future sampler
implementations without claiming they exist. `GridOptimizationStrategy` is
unchanged.

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
