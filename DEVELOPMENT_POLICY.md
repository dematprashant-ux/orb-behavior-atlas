# Development Policy

## 1. Purpose

This policy governs repository evolution: package maintenance, activation, and
integration scope. It does not define engine domain behavior, replace engine
documentation, or change any public contract. It is the single authoritative
source for active, shared, and frozen package maintenance status.

## 2. Package Status

Status is based on the current package structure and committed milestone work.
`optimization` and `walk_forward` are components of `src/engines/backtesting`;
they are not standalone top-level packages.

| Package | Status | Current role | Objective activation condition |
| --- | --- | --- | --- |
| `src/engines/data` | ACTIVE | Canonical market-data models, provider, normalization, validation, sessions, quality, and orchestration | N/A while approved Data Engine work continues |
| `src/engines/research` | ACTIVE | Immutable ORB facts, atlases, descriptive statistics, and CSV-to-atlas composition | N/A while approved Research Engine work continues |
| `src/core` | SHARED / CONSTRAINED | Cross-engine configuration, constants, logging, and generic persistence errors | An approved cross-engine requirement that cannot belong to one engine |
| `src/engines/strategy` | FROZEN | Strategy facts, parameter-space contracts, and deterministic candidate generation | An approved Research or Validation capability requires a strategy change |
| `src/engines/backtesting` | FROZEN | Backtest, optimization, reporting, and walk-forward contracts and composition | An approved active capability requires backtesting evaluation or reporting behavior |
| `src/engines/backtesting/walk_forward` | FROZEN | Backtesting's chronological split, execution-contract, analytics, and report components | An approved active capability requires walk-forward behavior |
| `src/engines/execution` | FROZEN | Immutable execution requests, results, and completed-trade facts | An approved strategy capability requires execution-domain behavior |
| `src/engines/performance` | FROZEN | PnL, performance, equity, drawdown, risk, and report artifacts | An approved consumer requires a behavior-preserving performance change |
| `src/engines/portfolio` | FROZEN | Portfolio allocation, equity, analytics, reporting, and pipeline artifacts | An approved validated strategy capability requires portfolio behavior |

ACTIVE packages MAY evolve only through approved milestones. SHARED /
CONSTRAINED code MUST remain minimal, technology-neutral where applicable, and
MUST NOT become a convenience location for engine-specific behavior.

## 3. Freeze Definition

FROZEN means **no proactive evolution; only reactive maintenance**. A frozen
package MAY be imported, inspected, executed, tested, and minimally repaired.
FROZEN does not mean deprecated, abandoned, or production-validated.

## 4. Allowed Frozen-Package Changes

Frozen-package changes MUST be narrowly justified. They MAY include:

- a minimal compatibility repair caused by an approved upstream change;
- a confirmed bug repair that preserves intended existing behavior;
- tests directly protecting that repair;
- changes required by an approved activation charter; and
- documentation corrections.

## 5. Prohibited Frozen-Package Changes

Frozen packages MUST NOT receive speculative features, convenience APIs,
generalized frameworks, style-only refactors, configurability without an active
consumer, unrelated cleanup, “while here” improvements, or expansion based
only on hypothetical future use.

## 6. Upstream Authority

Active upstream domain models remain authoritative. Work MUST NOT preserve or
distort an active model solely for compatibility with speculative frozen
consumers. If an approved upstream change breaks a frozen package, that package
MUST receive only the smallest behavior-preserving compatibility adaptation.

## 7. Compatibility Breakage Workflow

For an approved active-package change, maintainers MUST:

1. make the approved active-package change;
2. run the complete committed test suite;
3. leave frozen code unchanged when it does not fail;
4. apply the smallest behavior-preserving repair when frozen code fails because
   of that approved upstream change;
5. add or update only tests needed to prove compatibility;
6. avoid introducing new frozen-package capability; and
7. keep a reasonably small repair in the causing milestone.

Larger incompatibilities MUST be reported for a separate decision rather than
silently expanding scope. Compatibility maintenance is not package activation.

## 8. CI and Test Policy

All committed tests MUST remain enabled on `main`, and frozen-package tests
MUST remain green. Package status does not exempt tests from repository health.
Maintainers MUST NOT skip, weaken, delete, or mark tests expected-failure
because a package is frozen. New frozen-package tests require a confirmed
defect, compatibility repair, or approved activation charter; speculative test
expansion is prohibited.

The repository currently has no configured CI workflow steps in
`.github/workflows/ci.yml`. These requirements are therefore a repository
health policy, not a claim about a specific external CI implementation.

Validation summaries SHOULD report the Python version, Python executable,
Pytest version, full-suite test count, full-suite duration, slowest tests when
practical, and unavailable validation tools.

## 9. Activation Charter

Behavioral expansion of a frozen package requires an activation charter before
implementation. The charter MUST define:

- the package being activated;
- the concrete upstream trigger and reason for activation;
- the exact capability being introduced;
- allowed changes and explicit exclusions;
- acceptance criteria and required validation; and
- the automatic refreeze condition.

Compatibility-only maintenance does not require a full activation charter.

## 10. Scope Traceability

Every frozen-package file changed during maintenance or activation MUST map to
a demonstrated compatibility failure, a confirmed defect, or an
activation-charter acceptance criterion. Unrelated defects and opportunities
MUST be reported separately without modification.

## 11. Automatic Refreeze

Activation is temporary. A package automatically returns to FROZEN when its
activation charter’s acceptance criteria pass, validation succeeds, and the
milestone is merged. There is no indefinite “temporarily active” state.

## 12. Research Experimentation

Consumption is distinct from modification. Without activation, maintainers MAY
import frozen code, use existing public APIs, perform notebook exploration,
write temporary consumer-side adapters, and run disposable experiments that do
not modify the frozen package.

Changing frozen behavior, adding public APIs or general-purpose capabilities,
or committing package modifications for an experiment requires activation. A
quick experiment MUST NOT automatically become repository architecture.

## 13. Repository Health

`main` MUST remain green. Frozen code MUST NOT be allowed to fail indefinitely;
documentation-only status does not excuse broken imports or failed committed
tests. Unrelated untracked files MUST NOT be staged by milestone work. Active
work SHOULD NOT proactively modernize frozen packages.

## 14. Minimal Integration Principle

When a frozen package is activated, maintainers MUST implement only the
smallest change required by the approved upstream capability, validate it,
merge it, and refreeze the package.
