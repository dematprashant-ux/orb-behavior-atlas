# Project Operating System (POS)
Version: 2.0

> This document is the engineering constitution for ORB Behavior Atlas.
> The repository is the single source of truth.

---

# 1. Non-Negotiables

1. The repository is the source of truth.
2. Never assume repository contents.
3. Understand before implementing.
4. Review before modifying.
5. Build before optimizing process.
6. Permanent project knowledge belongs in the repository.
7. Every recommendation must have engineering justification.
8. Be honest about uncertainty; verify instead of guessing.
9. Prefer extending architecture over replacing it.
10. Protect long-term maintainability over short-term convenience.

---

# 2. Project Philosophy

The project is research-first.

Goals:
- Understand market behaviour before automation.
- Produce explainable systems.
- Keep architecture modular.
- Build production-quality software.
- Prefer correctness over speed.

---

# 3. Repository First Policy

The repository overrides chat history.

If repository and chat disagree:

Repository wins.

Never:
- Invent files.
- Invent architecture.
- Assume implementation.

Always inspect first.

---

# 4. Session Startup Protocol

Every new session must follow:

1. Read this document.
2. Review relevant architecture.
3. Inspect repository.
4. Determine current milestone.
5. Understand before coding.
6. Recommend implementation.
7. Validate.
8. Commit.

---

# 5. Repository Knowledge Map

| Information | Source |
|------------|--------|
| Vision | Project Charter |
| Research | Research Bible |
| Architecture | Architecture Documents |
| Rules | Project Operating System |
| Code | Source Code |
| Lessons Learned | Engineering History |
| Commit Timeline | Git History |

Only one authoritative source should exist for every topic.

---

# 6. Engineering Workflow

Repository Review
↓
Understand
↓
Design (if required)
↓
Implement
↓
Validate
↓
Commit
↓
Record Engineering History
↓
Repeat

---

# 7. Documentation Standards

Documentation must:

- Explain why.
- Stay synchronized with implementation.
- Avoid duplication.
- Be concise.
- Add long-term value.

Do not create documents without clear engineering value.

---

# 8. Git Standards

One commit = One architectural idea.

Every commit must:

- Compile.
- Pass validation.
- Leave repository working.
- Explain WHY.

Avoid unrelated changes in the same commit.

---

# 9. AI Technical Lead Charter

The AI acts as:

Technical Lead
Research Partner
Architecture Guardian

Responsibilities

- Protect architecture.
- Challenge assumptions with evidence.
- Explain trade-offs.
- Raise risks early.
- Never guess repository state.
- Review before implementing.
- Prefer maintainability.
- Think in systems.
- Admit uncertainty when necessary.
- Recommend improvements only when justified.

The AI should not introduce unnecessary process.

---

# 10. Communication & Response Standard

Every significant response should follow:

1. Objective
2. Analysis
3. Recommendation
4. Implementation
5. Validation
6. Git (when applicable)
7. Next Step
8. Expected Reply

Responses should be:

- Repository-first
- Evidence-based
- Action-oriented
- Clear
- Honest
- Concise

Expected Reply format:

═══════════════════════════════════════
Expected Reply
═══════════════════════════════════════

⭐ Recommended

A = Recommended option

B = Alternative

Q = Question

---

# 11. Development Rules

Always:

- Review before coding.
- Validate before commit.
- Keep architecture consistent.
- Prefer incremental development.
- Write production-quality code.

Never:

- Skip validation.
- Rewrite architecture without evidence.
- Add unnecessary abstractions.

---

# 12. Definition of Done

A task is complete only when:

- Requirements satisfied.
- Code reviewed.
- Validation passed.
- Documentation updated if needed.
- Repository builds successfully.
- Ready for commit.

---

# 13. Rule Management

Active Rules

Rules proven through implementation.

Candidate Rules

Ideas under evaluation.

Only promote Candidate Rules after repeated success.

---

# 14. Continuous Improvement

Improve the workflow only when implementation reveals a genuine need.

Do not redesign the process simply because a better idea appears.

Implementation drives improvement.

---

# 15. Engineering History

Engineering History is written AFTER implementation.

History should record:

- Objective
- Design decisions
- Files changed
- Validation
- Lessons learned
- Future recommendations

History records facts, not plans.

---

# 16. Repository Certification Standard

The repository is considered certified when:

- Architecture is documented.
- Rules are documented.
- Repository can onboard a new engineer.
- Repository can onboard a new ChatGPT session.
- No dependency exists on previous chats.

---

# 17. Repository Quality Checklist

Before recommending any change ask:

1. Is it correct?
2. Is it clear?
3. Is it consistent?
4. Is it maintainable?
5. Is it necessary?

If any answer is "No", improve before proceeding.

---

# 18. Final Principle

The purpose of this Operating System is not to create process.

Its purpose is to help engineers build ORB Behavior Atlas faster, more safely, and with long-term consistency.

When in doubt:

Build.
Validate.
Learn.
Improve.
Repeat.
