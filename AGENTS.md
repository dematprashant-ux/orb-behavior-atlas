# ORB Behavior Atlas - Engineering Instructions

## Repository First

Always inspect the repository before making changes.

Read relevant documentation before implementing.

Never assume architecture.

---

## Development Principles

- Production-quality code only.
- Strong type hints.
- Comprehensive docstrings.
- Small focused modules.
- One architectural idea per commit.
- Keep the repository buildable after every change.

---

## Workflow

For every task:

1. Review documentation.
2. Review existing implementation.
3. Explain the plan.
4. Implement.
5. Validate.
6. Summarize changes.

---

## Architecture

Follow the repository architecture.

Do not introduce new patterns without justification.

Current engine layout:

src/
    engines/
        data/
        orb/
        event/
        behavior/
        research/
        validation/
        strategy/
        execution/

---

## Validation

Before finishing:

- imports pass
- typing is correct
- formatting is consistent
- no circular imports