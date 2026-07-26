# Development Guide

**Project:** ORB Behavior Atlas  
**Document Version:** 1.0  
**Status:** Draft  
**Owner:** Prashant Gawade  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document serves as the day-to-day development handbook for the ORB Behavior Atlas.

It defines the standard workflow for implementing, testing, documenting, reviewing, and maintaining the platform while ensuring consistency with the project's architecture and governance.

---

# 2. Development Philosophy

Development follows a research-first approach.

Every implementation should follow this sequence:

```
Requirement

↓

Design

↓

Implementation

↓

Testing

↓

Documentation

↓

Review

↓

Merge
```

No implementation should skip any stage.

---

# 3. Repository Structure

```
banknifty-orb-behavior-atlas/

├── docs/
├── src/
├── tests/
├── configs/
├── scripts/
├── notebooks/
├── data/
├── logs/
├── reports/
├── README.md
├── CHANGELOG.md
├── LICENSE
└── DECISIONS.md
```

Each directory has a single responsibility.

---

# 4. Local Development Environment

Recommended setup:

- Python 3.11+
- Git
- VS Code
- Virtual Environment
- pytest
- Ruff
- Black
- MyPy

Development environments should be reproducible.

The repository pins the supported local minor version to Python 3.11 through
`.python-version`. `pyproject.toml` requires Python 3.11 or newer, and the
configured Black and Ruff targets are Python 3.11. Python 3.9 is unsupported:
the repository uses Python 3.10+ language and runtime features and declares
Python 3.11+ support, so Python 3.9 will fail before or during test collection.

Create the canonical local environment with the explicitly selected
interpreter. Do not assume that bare `python` or `python3` selects Python 3.11.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Confirm the active environment before validation:

```bash
python --version
python -m pytest --version
python -c "import sys; print(sys.executable)"
```

For diagnostic observation and baseline measurement, run:

```bash
python -m pytest --durations=20
```

This command is not a hard performance gate.

---

# 5. Branching Workflow

Use the following branch structure:

```
main
develop
feature/*
release/*
hotfix/*
```

Feature work should never be committed directly to `main`.

---

# 6. Daily Development Workflow

For every feature:

1. Pull latest changes
2. Create feature branch
3. Implement feature
4. Write tests
5. Update documentation
6. Run validation
7. Commit changes
8. Open Pull Request
9. Review
10. Merge

---

# 7. Coding Workflow

During implementation:

- Follow Coding Standards
- Keep commits small
- Avoid unrelated changes
- Use descriptive names
- Prefer modular design
- Keep functions focused

Every change should improve maintainability.

---

# 8. Testing Workflow

Before every commit:

- Run unit tests
- Run integration tests
- Verify regression suite
- Confirm no failing tests

No failing tests should be merged.

---

# 9. Documentation Workflow

Documentation should be updated whenever:

- New feature added
- Existing behavior changes
- API changes
- Architecture changes
- Configuration changes

Documentation changes should accompany code changes.

---

# 10. Pull Request Process

Every Pull Request should include:

- Summary
- Motivation
- Scope
- Testing performed
- Documentation updated
- Related issues

Pull Requests should remain focused.

---

# 11. Issue Management

Every issue should include:

- Title
- Description
- Expected behavior
- Actual behavior
- Steps to reproduce
- Severity
- Labels

Issues should be traceable.

---

# 12. Debugging Practices

When debugging:

- Reproduce consistently
- Isolate the cause
- Add temporary logging if needed
- Verify the fix
- Add regression tests

Debugging should improve future reliability.

---

# 13. Configuration Management

Configuration should:

- Be external
- Be documented
- Support multiple environments
- Avoid hardcoded secrets

Environment-specific values belong in configuration files.

---

# 14. Dependency Management

When adding dependencies:

- Verify maintenance status
- Check license compatibility
- Pin versions
- Document purpose

Avoid unnecessary dependencies.

---

# 15. Code Review Guidelines

Reviewers should verify:

- Correctness
- Readability
- Test coverage
- Documentation
- Performance
- Error handling
- Standards compliance

Reviews should improve code quality.

---

# 16. Best Practices

Developers should:

- Write readable code
- Keep modules independent
- Prefer explicit behavior
- Handle errors gracefully
- Remove dead code
- Keep documentation current

Consistency is more valuable than cleverness.

---

# 17. Common Pitfalls

Avoid:

- Large commits
- Hidden side effects
- Duplicate logic
- Untested features
- Incomplete documentation
- Premature optimization

These reduce maintainability.

---

# 18. Developer Checklist

Before marking work complete:

- Implementation finished
- Tests passing
- Documentation updated
- Linting passed
- Review completed
- Commit message written
- Related issue updated

Only then is the work considered complete.

---

# 19. Continuous Improvement

Developers are encouraged to improve:

- Documentation
- Tooling
- Test coverage
- Code quality
- Build process
- Developer experience

Improvements should align with project governance.

---

# 20. Future Enhancements

Future improvements may include:

- Automated development environment setup
- Pre-commit hooks
- Continuous code quality analysis
- Developer dashboards
- AI-assisted code review
- Automated documentation generation

Enhancements should simplify development without reducing quality.

---

# 21. Conclusion

The Development Guide provides the practical workflow for building and maintaining the ORB Behavior Atlas.

By following standardized development, testing, documentation, review, and collaboration practices, contributors can ensure the platform remains consistent, reliable, and aligned with its long-term research-first vision.
