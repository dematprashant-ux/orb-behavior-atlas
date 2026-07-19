# Hypothesis Register

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

The Hypothesis Register is the central catalog of all research ideas investigated by the ORB Behavior Atlas.

Every hypothesis follows a standardized lifecycle from creation through validation or retirement, ensuring complete traceability and reproducibility.

---

# 2. Guiding Principles

Every hypothesis must be:

- Clearly stated
- Testable
- Falsifiable
- Independent
- Reproducible
- Version controlled

No hypothesis may bypass the validation framework.

---

# 3. Hypothesis Lifecycle

```
Idea

↓

Draft

↓

Research

↓

Statistical Analysis

↓

Validation

↓

Accepted / Rejected

↓

Archived
```

---

# 4. Status Definitions

| Status | Meaning |
|---------|---------|
| Draft | Idea has been created but not tested |
| Active | Currently under investigation |
| Validating | Under walk-forward or out-of-sample testing |
| Accepted | Passed all validation requirements |
| Rejected | Failed validation |
| Retired | Previously accepted but no longer valid |
| Archived | Preserved for historical reference |

---

# 5. Priority Levels

| Priority | Description |
|----------|-------------|
| Critical | High research value |
| High | Strong expected impact |
| Medium | Normal research priority |
| Low | Exploratory idea |

---

# 6. Hypothesis Identifier

Each hypothesis receives a permanent identifier.

Format:

```
HYP-0001
HYP-0002
HYP-0003
```

Identifiers are never reused.

---

# 7. Required Fields

Every hypothesis must include:

| Field | Description |
|--------|-------------|
| ID | Unique identifier |
| Title | Short descriptive name |
| Description | Research question |
| Motivation | Why it is being tested |
| Expected Outcome | Predicted behavior |
| Related Levels | ORB levels involved |
| Related Events | Event types involved |
| Related Behaviors | Behavior types involved |
| Priority | Critical / High / Medium / Low |
| Author | Research owner |
| Date Created | Creation date |
| Current Status | Lifecycle stage |

---

# 8. Success Criteria

Before testing begins, define measurable success criteria.

Examples:

- Win rate above predefined threshold
- Positive expectancy
- Stable across market regimes
- Statistically significant
- Sufficient sample size

Success criteria must not change after research begins.

---

# 9. Failure Criteria

A hypothesis fails if it demonstrates:

- Negative expectancy
- Insufficient evidence
- Poor walk-forward performance
- Lack of statistical significance
- Instability across regimes

Failed hypotheses remain documented.

---

# 10. Validation References

Each hypothesis must reference:

- Research Log
- Validation Report
- Evidence Score
- Statistical Report
- Decision Record

This creates a complete audit trail.

---

# 11. Decision Log

Every major decision must be recorded.

Example:

| Date | Decision |
|------|----------|
| 2026-07-18 | Hypothesis created |
| 2026-08-02 | Historical testing completed |
| 2026-08-10 | Walk-forward validation passed |
| 2026-08-20 | Accepted for production research |

---

# 12. Retirement Rules

Accepted hypotheses may be retired if:

- Performance deteriorates
- Market structure changes
- Better evidence supersedes them
- Validation framework no longer supports them

Retirement does not delete historical records.

---

# 13. Standard Hypothesis Template

```
ID:

Title:

Research Question:

Description:

Motivation:

Expected Outcome:

Related ORB Levels:

Related Events:

Related Behaviors:

Priority:

Author:

Date Created:

Status:

Success Criteria:

Failure Criteria:

Research Notes:

Validation References:

Decision History:

Final Conclusion:
```

---

# 14. Version Control

Updates to a hypothesis must preserve history.

Changes should include:

- Date
- Reason
- Author
- Version

Historical versions must remain accessible.

---

# 15. Future Enhancements

Future versions may include:

- Automated hypothesis generation
- Bayesian confidence updates
- Similarity detection
- Duplicate hypothesis prevention
- Dependency mapping
- Research effort estimation

---

# 16. Conclusion

The Hypothesis Register provides a structured, auditable process for managing research ideas throughout their lifecycle. It ensures every conclusion is supported by evidence, validation, and documented decisions before contributing to the ORB Behavior Atlas.
