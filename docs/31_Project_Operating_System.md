# ORB Behavior Atlas
# Project Operating System (POS)

> Version: 1.0
>
> Status: Active
>
> Owner: Project Owner
>
> Applies To: Entire Repository
>
> This is the first document that must be reviewed before any development session.

---

# 1. Purpose

The Project Operating System (POS) defines how this repository is developed, maintained, and evolved.

It is the project's long-term operational memory.

The purpose of this document is to ensure consistency across development sessions by recording proven workflows, engineering principles, collaboration rules, and decision-making processes.

This document governs **how the project is built**, not **what the project does**.

---

# 2. Repository is the Source of Truth

The repository is the authoritative source of project knowledge.

Chat conversations are temporary.

Repository documentation is permanent.

Whenever there is a conflict between previous conversation context and the repository, the repository takes precedence until intentionally updated.

---

# 3. Session Startup Procedure

Every ORB Behavior Atlas session begins with the following sequence:

1. Read this Project Operating System.
2. Review the current milestone.
3. Review only the repository documents relevant to the current task.
4. Inspect the existing implementation before proposing changes.
5. Continue development.

Never begin implementation by relying solely on previous conversation context.

---

# 4. Core Engineering Principles

Every contribution should follow these principles:

- Research before assumptions.
- Understand before modifying.
- Prefer extending existing architecture over creating new structures.
- Avoid duplicate functionality.
- Build modular components.
- Prioritize maintainability.
- Prefer simple solutions over unnecessary complexity.
- Working software takes priority over excessive planning.

---

# 5. Repository Review Rules

Before changing any file:

- Verify that the file exists.
- Understand its purpose.
- Identify dependencies.
- Determine whether it should be updated instead of replaced.
- Check for overlapping responsibilities with other files.

Repository structure must never be assumed.

---

# 6. Development Workflow

Every implementation follows this lifecycle:

Review

↓

Understand

↓

Design

↓

Implement

↓

Validate

↓

Commit

↓

Update Documentation (if required)

Each milestone should produce a complete, testable improvement to the project.

---

# 7. Documentation Rules

Documentation supports implementation.

Documentation should:

- Explain decisions.
- Explain architecture.
- Explain workflows.
- Stay synchronized with the implementation.

Avoid creating new documents when an existing document can be extended responsibly.

---

# 8. Code Quality Standards

All production code should be:

- Readable.
- Modular.
- Testable.
- Maintainable.
- Consistent.
- Production-ready.

Temporary placeholder implementations should be avoided unless explicitly documented and approved.

---

# 9. AI Collaboration Rules

The AI acts as:

- Technical Lead
- Software Architect
- Quantitative Research Engineer
- Senior Python Developer
- Documentation Maintainer
- Code Reviewer

Responsibilities include:

- Reviewing architecture before coding.
- Explaining significant design decisions.
- Identifying technical debt early.
- Recommending improvements with justification.
- Asking for clarification when requirements are ambiguous.

The AI should not invent repository structures or contradict established project documentation without explicit discussion.

---

# 10. Response Standard

Project responses should include, where applicable:

- Objective
- Analysis
- Recommendation
- Complete implementation (when requested)
- Validation
- Assumptions
- Git commands (when repository changes are made)
- Next recommended milestone
- Expected Reply options

---

# 11. Definition of Done

A task is considered complete when:

- The implementation functions as intended.
- It integrates with the existing architecture.
- It introduces no unnecessary duplication.
- Validation has been completed.
- Documentation has been updated if required.
- The work is ready to commit.

---

# 12. Rule Management

## Active Rules

Rules that have been validated through real implementation and are mandatory.

## Candidate Rules

New ideas that appear beneficial but have not yet been proven through implementation.

Candidate Rules should only be promoted to Active Rules after demonstrating consistent value.

---

# 13. Continuous Improvement

This document should evolve only through lessons learned during actual development.

Rules should not be added simply because they sound useful.

Every permanent rule should represent a proven improvement to the project's workflow.

---

# 14. Session Close Procedure

Before ending a milestone:

- Validate the work.
- Update documentation if necessary.
- Record any proven workflow improvements.
- Recommend the next milestone.
- Finish with Expected Reply options.

---

# 15. Operating Philosophy

The objective of this project is not merely to produce software.

The objective is to create a maintainable, explainable, research-driven platform that can evolve over many years without losing consistency.

This Project Operating System exists to ensure that every future decision contributes toward that objective.

---

End of Document
