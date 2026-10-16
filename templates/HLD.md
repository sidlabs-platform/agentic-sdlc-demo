# High-Level Design (HLD)

| Field | Value |
| --- | --- |
| Application / Version / Date / Author | [Values] |
| BRD reference | [Accepted version] |

## 1. Design Overview & Goals
[Purpose, scope, design goals, constraints and explicitly excluded features.]

## 2. Architecture Diagram
[Mermaid diagram of actual components, external systems and trust boundaries.]

## 3. System Components
| ID | Responsibility | Technology | Requirement IDs | LLD |
| --- | --- | --- | --- | --- |
| COMP-001 | [Bounded responsibility] | [Selected technology] | BRD-FR-001 | [Relative link] |

## 4. Component Interactions
[Communication patterns, contracts, authentication and sequence diagrams for
key user journeys; include error paths.]

## 5. Data Flow & Lifecycle
[Data-flow diagram; schemas, persistence, ownership, migrations, retention,
sensitivity and deletion.]

## 6. External Integrations & Resilience
[Required integrations only: contracts, auth, timeouts, rate limits, retries,
idempotency, fallbacks and observability. N/A with reason if none.]

## 7. Architecture / Stack Decision
| Layer / decision | Alternatives | Selected technology / version | Rationale / trade-offs |
| --- | --- | --- | --- |
| Language / runtime | [Options] | [Choice] | [Brief-derived rationale] |
| Interfaces / persistence / UI | [Options] | [Choices or N/A] | [Rationale] |
| Packages / tests / quality / security | [Options] | [Tools] | [Coverage and limits] |

[Source/test layout, package management and lockfiles, supported runner
(`ubuntu-latest`, `windows-latest`, or `macos-latest`), runtime installation,
setup/build/lint/typecheck/test/security expectations, CodeQL supported language
matrix/build needs or alternative scanner, actual Dependabot ecosystems.]
Require explicit true/false entitlement decisions for dependency review and
CodeQL, retaining their stable policy checks. False CodeQL means Ruff S for
template Python plus selected app security commands, not universal coverage.
App source roots cannot be template-owned directories.
Choose the positive JUnit `minimum_tests` and repository-relative `.xml` report
path for the configured toolchain's `test_report`; do not assume process exit
success alone demonstrates real tests.

## 8. Deployment & Operations Architecture
[Local execution, environments, configuration, health, backup, restore,
monitoring and provider-neutral deployment interface. Deployment remains
disabled until configured; reference release/rollback procedure.]

## 9. Security Considerations
[Assets, threat actors, trust boundaries, authorization, secrets, data
protection, supply chain, safe logs and abuse resistance.]

## 10. Design Decisions & Trade-offs
| ID | Decision | Options | Chosen approach | Consequences |
| --- | --- | --- | --- | --- |
| DD-001 | [Decision] | [Options] | [Choice] | [Rationale / risks] |

## 11. Traceability & Open Decisions
| BRD requirement | Component / control | LLD / verification |
| --- | --- | --- |
| BRD-FR-001 | COMP-001 | [Link / method] |

[Account for every requirement; record blockers rather than inventing answers.]
