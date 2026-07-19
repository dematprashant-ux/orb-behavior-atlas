# Edge Repository

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

The Edge Repository is the permanent catalog of all statistically validated market edges discovered by the ORB Behavior Atlas.

Only edges that successfully complete the Validation Framework are eligible for inclusion.

The repository serves as the single source of truth for production-ready trading knowledge.

---

# 2. Edge Philosophy

An edge is not an idea.

An edge is not a strategy.

An edge is a statistically validated market behavior with demonstrated predictive value.

Every edge must be:

- Measurable
- Reproducible
- Statistically significant
- Walk-forward validated
- Out-of-sample validated
- Regime tested

---

# 3. Edge Lifecycle

```
Hypothesis

↓

Research

↓

Behavior Discovery

↓

Validation

↓

Accepted Edge

↓

Production Monitoring

↓

Retired
```

---

# 4. Edge Identifier

Every edge receives a permanent unique identifier.

Format:

```
EDGE-0001
EDGE-0002
EDGE-0003
```

Identifiers are never reused.

---

# 5. Edge Classification

| Class | Description |
|--------|-------------|
| Experimental | Initial evidence |
| Candidate | Promising but incomplete |
| Validated | Passed validation |
| Production | Approved for strategy generation |
| Retired | No longer reliable |

---

# 6. Required Fields

Every edge must contain:

| Field | Description |
|--------|-------------|
| Edge ID | Permanent identifier |
| Title | Short descriptive name |
| Description | Summary of the edge |
| Related Hypothesis | Source hypothesis |
| Related Behaviors | Supporting behaviors |
| Related Events | Supporting events |
| Related ORB Levels | Levels involved |
| Direction | Bullish / Bearish / Neutral |
| Created Date | Creation date |
| Current Status | Lifecycle stage |
| Owner | Research owner |

---

# 7. Statistical Metrics

Each edge records:

- Sample Size
- Win Rate
- Loss Rate
- Expectancy
- Average Return
- Median Return
- Maximum Drawdown
- Profit Factor
- Sharpe Ratio (if applicable)
- Maximum Favorable Excursion (MFE)
- Maximum Adverse Excursion (MAE)

---

# 8. Validation Summary

Every edge must reference completed validation:

- Historical Validation
- Statistical Validation
- Walk-Forward Validation
- Out-of-Sample Validation
- Regime Validation

Each stage should record:

- Pass / Fail
- Validation Date
- Notes

---

# 9. Confidence Score

Each edge receives a confidence score between **0 and 100**.

Suggested contributors:

- Sample size
- Statistical significance
- Walk-forward stability
- Out-of-sample performance
- Regime consistency

Higher scores indicate greater confidence.

---

# 10. Evidence Score

The Evidence Score measures the overall strength of supporting research.

Suggested inputs:

- Number of independent validations
- Reproducibility
- Robustness
- Predictive accuracy
- Stability over time

Range:

```
0–100
```

---

# 11. Dependencies

Each edge should reference:

- Hypothesis ID(s)
- Behavior ID(s)
- Event ID(s)
- Validation Report(s)
- Research Log(s)
- Decision Record(s)

This provides full traceability.

---

# 12. Production Monitoring

Approved edges should be monitored continuously.

Recommended metrics:

- Rolling win rate
- Rolling expectancy
- Drawdown
- Prediction accuracy
- Regime performance
- Drift detection

Monitoring results should be stored with timestamps.

---

# 13. Retirement Rules

An edge should be retired if:

- Statistical significance is lost
- Walk-forward performance deteriorates
- Regime stability breaks down
- Better evidence replaces it
- Persistent underperformance is observed

Retired edges remain in the repository for historical analysis.

---

# 14. Standard Edge Template

```
Edge ID:

Title:

Description:

Related Hypothesis:

Related Behaviors:

Related Events:

Related ORB Levels:

Direction:

Status:

Created Date:

Owner:

Sample Size:

Win Rate:

Loss Rate:

Expectancy:

Average Return:

Maximum Drawdown:

Profit Factor:

MFE:

MAE:

Confidence Score:

Evidence Score:

Validation Summary:

Production Notes:

Monitoring History:

Retirement Status:

Final Remarks:
```

---

# 15. Version Control

Every modification must record:

- Date
- Version
- Author
- Reason for Change

Historical versions must remain available.

---

# 16. Future Enhancements

Future versions may include:

- Automated edge ranking
- Portfolio-level edge interactions
- Correlation analysis between edges
- Edge decay prediction
- AI-assisted edge discovery
- Live performance dashboards

---

# 17. Conclusion

The Edge Repository is the permanent knowledge base of validated market edges.

It ensures that every production decision is backed by documented evidence, rigorous validation, and continuous monitoring, creating a reliable foundation for future strategy generation.
