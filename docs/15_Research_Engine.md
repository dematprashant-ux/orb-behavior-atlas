# Research Engine

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

The Research Engine is the scientific core of the ORB Behavior Atlas.

Its responsibility is to transform validated market behaviors into measurable evidence through controlled experiments, statistical analysis, and hypothesis testing.

The Research Engine discovers facts.

It does not make trading decisions.

---

# 2. Responsibilities

The Research Engine is responsible for:

- Executing research hypotheses
- Running experiments
- Collecting observations
- Computing statistics
- Measuring behavior performance
- Recording research results
- Producing reproducible evidence
- Handing results to the Validation Engine

---

# 3. Inputs

The Research Engine accepts:

- Behavior Objects
- Event Objects
- ORB Objects
- Trading Sessions
- Hypothesis Definitions

Inputs must originate from validated upstream engines.

---

# 4. Research Workflow

```
Hypothesis

↓

Experiment Design

↓

Behavior Selection

↓

Data Collection

↓

Statistical Analysis

↓

Research Report

↓

Validation Engine
```

---

# 5. Experiment Lifecycle

Each experiment progresses through the following stages:

```
Draft

↓

Running

↓

Completed

↓

Validated

↓

Archived
```

Experiments are immutable after completion.

---

# 6. Hypothesis Execution

Each experiment is linked to exactly one primary hypothesis.

Execution includes:

- Loading required data
- Selecting matching behaviors
- Applying research rules
- Collecting observations
- Computing metrics
- Recording findings

Hypothesis definitions remain external to the engine.

---

# 7. Statistical Analysis Pipeline

For every experiment the engine computes:

- Sample Size
- Frequency
- Probability
- Mean
- Median
- Standard Deviation
- Variance
- Expectancy
- Win Rate
- Loss Rate
- Maximum Favorable Excursion (MFE)
- Maximum Adverse Excursion (MAE)
- Maximum Drawdown
- Confidence Interval
- p-value

Additional metrics may be added without changing existing interfaces.

---

# 8. Research Object

Each experiment produces one Research Object.

| Field | Description |
|--------|-------------|
| research_id | Permanent identifier |
| hypothesis_id | Source hypothesis |
| session_range | Data analyzed |
| behavior_count | Behaviors evaluated |
| sample_size | Number of observations |
| methodology | Experiment description |
| statistics | Computed metrics |
| findings | Research results |
| status | Draft / Running / Completed |
| metadata | Additional information |

Research objects are immutable after completion.

---

# 9. Output

Each completed experiment produces:

- Research Report
- Statistical Summary
- Observation Dataset
- Validation Package
- Decision Recommendation

Outputs become inputs for the Validation Engine.

---

# 10. Validation Handoff

The Research Engine never determines whether an edge is valid.

Instead, it forwards completed research packages to the Validation Engine containing:

- Hypothesis
- Methodology
- Statistics
- Supporting Behaviors
- Supporting Events
- Research Findings

---

# 11. Public Interfaces

The Research Engine should expose functions equivalent to:

```
run_experiment()

get_experiment()

get_statistics()

get_findings()

export_research()

list_experiments()
```

Interfaces should remain stable across versions.

---

# 12. Validation Rules

Every experiment must satisfy:

- Valid hypothesis
- Valid behavior references
- Valid event references
- Reproducible methodology
- Sufficient sample size
- Complete statistical output

Incomplete experiments cannot proceed to validation.

---

# 13. Error Handling

The engine should detect and report:

- Missing hypothesis
- Missing behaviors
- Invalid event references
- Insufficient data
- Statistical computation failures
- Invalid experiment configuration

Errors must be logged with sufficient diagnostic information.

---

# 14. Performance Goals

The Research Engine should provide:

- Deterministic execution
- Reproducible experiments
- Efficient batch processing
- Scalable statistical computation
- Low memory overhead where practical

Performance optimizations must never compromise reproducibility.

---

# 15. Dependencies

Depends on:

- Data Engine
- ORB Engine
- Event Engine
- Behavior Engine
- Hypothesis Register

Provides outputs to:

- Validation Engine
- Edge Repository
- Research Log

---

# 16. Design Principles

The Research Engine must always be:

- Scientific
- Deterministic
- Reproducible
- Strategy-independent
- Fully auditable
- Evidence-driven

Research conclusions must arise solely from observed data and documented methodology.

---

# 17. Future Enhancements

Future versions may include:

- Automated hypothesis generation
- Bayesian inference
- Monte Carlo simulation
- Bootstrap resampling
- Cross-validation
- Parameter sweep automation
- Parallel experiment execution
- AI-assisted research prioritization

---

# 18. Conclusion

The Research Engine is the scientific laboratory of the ORB Behavior Atlas.

It transforms market behaviors into measurable evidence through controlled experimentation and rigorous statistical analysis, providing the Validation Engine with the information required to determine whether a discovered behavior represents a genuine and reliable market edge.
