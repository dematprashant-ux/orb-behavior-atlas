# Validation Framework

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

The Validation Framework defines how research findings are evaluated before they are accepted as reliable market behaviors.

The goal is to prevent false discoveries, overfitting, and data mining bias.

No research result becomes an Edge until it successfully passes this framework.

---

# 2. Validation Philosophy

The objective of validation is **not** to prove a hypothesis correct.

The objective is to attempt to disprove it.

Only hypotheses that survive repeated testing become validated evidence.

---

# 3. Validation Pipeline

```
Research Question

↓

Hypothesis

↓

Historical Analysis

↓

Statistical Analysis

↓

Walk-Forward Validation

↓

Out-of-Sample Validation

↓

Regime Validation

↓

Edge Classification
```

---

# 4. Validation Levels

| Level | Description |
|--------|-------------|
| V1 | Historical Validation |
| V2 | Statistical Validation |
| V3 | Walk-Forward Validation |
| V4 | Out-of-Sample Validation |
| V5 | Regime Validation |
| V6 | Production Ready |

Every Edge must progress through these stages in order.

---

# 5. Historical Validation

Checks whether a behavior exists in historical data.

Requirements:

- Correct event sequence
- Minimum sample size
- No missing data
- Deterministic detection

---

# 6. Statistical Validation

Every research result should record:

- Sample Size
- Probability
- Mean
- Median
- Standard Deviation
- Expectancy
- Maximum Drawdown
- MFE
- MAE
- Confidence Interval
- p-value

---

# 7. Walk-Forward Validation

Training data and validation data must remain separated.

Example:

```
Years 1–9

↓

Research

↓

Freeze Rules

↓

Year 10

↓

Prediction

↓

Evaluation
```

Knowledge from Year 10 must never influence model creation.

---

# 8. Out-of-Sample Validation

Out-of-sample data must remain unseen during research.

Purpose:

Verify that discovered behaviors generalize beyond the development dataset.

---

# 9. Regime Validation

Behaviors should be evaluated across different market environments.

Example regimes:

- Trending
- Ranging
- High Volatility
- Low Volatility
- Expiry Days
- Gap Up
- Gap Down

A robust edge should remain reasonably stable across multiple regimes.

---

# 10. Sample Size Requirements

No conclusion should be accepted without an adequate number of observations.

Research reports must always include the exact sample size.

---

# 11. Confidence Scoring

Every validated behavior receives a confidence score.

Suggested inputs:

- Sample Size
- Statistical Significance
- Walk-Forward Success
- Out-of-Sample Success
- Regime Stability

Confidence Score Range:

0–100

---

# 12. Evidence Score

Each Edge receives an Evidence Score.

Suggested components:

- Statistical Strength
- Repeatability
- Stability
- Robustness
- Predictive Performance

Higher scores indicate stronger evidence.

---

# 13. Edge Classification

| Class | Meaning |
|--------|---------|
| Experimental | Initial observation |
| Candidate | Preliminary evidence |
| Validated | Passed validation framework |
| Production | Approved for strategy generation |
| Retired | No longer reliable |

---

# 14. Edge Retirement

An Edge should be retired if:

- Statistical significance deteriorates
- Walk-forward performance degrades
- Regime stability disappears
- Predictive performance declines consistently

Retired edges remain documented for historical reference.

---

# 15. Research Integrity Rules

The following are prohibited:

- Look-ahead bias
- Data leakage
- Curve fitting
- Manual cherry-picking
- Ignoring failed hypotheses
- Changing definitions after testing

---

# 16. Reporting Standards

Every research report must include:

- Research Question
- Hypothesis
- Sample Size
- Methodology
- Results
- Statistical Summary
- Validation Results
- Final Conclusion

---

# 17. Future Improvements

Future versions may include:

- Monte Carlo Simulation
- Bootstrap Analysis
- Bayesian Validation
- Probability Calibration
- Drift Detection
- Automated Edge Monitoring

---

# 18. Conclusion

The Validation Framework ensures that only statistically sound and reproducible market behaviors become candidate trading edges.

Its purpose is to maximize confidence while minimizing false discoveries.
