# Business Requirements Document (BRD)

| Field | Value |
| --- | --- |
| Title / Version / Date | [Application / version / date] |
| Author / Review status | [Author / draft or accepted evidence] |
| Source brief | [Root issue and application-brief.md reference] |

Replace every placeholder in a generated document; use N/A with rationale for
irrelevant sections. Do not invent material decisions.

## 1. Executive Summary

### Project Overview
[Problem, target audience, proposed outcomes; no assumed stack.]

### Business Objectives and Success Metrics
| KPI ID | Objective | Target | Measurement |
| --- | --- | --- | --- |
| KPI-001 | [Outcome] | [Measurable target] | [Method] |

## 2. Background & Context
[Current process, pain points, evidence and opportunity.]

## 3. Stakeholders, Personas & Journeys
| Persona / stakeholder | Responsibility / need | Journey | Influence |
| --- | --- | --- | --- |
| [Role from brief] | [Need] | [Steps and outcome] | [Level] |

## 4. Scope
### In Scope
[Prioritized capabilities.]
### Out of Scope / Deferred
[Explicit exclusions.]
### Assumptions, Constraints & Dependencies
[Distinguish confirmed constraints from assumptions needing writer decisions.]

## 5. Use Cases
| ID | Actors | Preconditions / flow | Outcome | Priority |
| --- | --- | --- | --- | --- |
| UC-001 | [Persona] | [Journey] | [Outcome] | Must / Should / Could |

## 6. Functional Requirements
| ID | Requirement | Priority | Measurable acceptance criteria |
| --- | --- | --- | --- |
| BRD-FR-001 | [Behavior] | Must | [Given / When / Then] |

## 7. Non-Functional Requirements
| ID | Category | Requirement / target | Verification |
| --- | --- | --- | --- |
| BRD-NFR-001 | [Security / usability / performance / reliability] | [Target] | [Method] |

Include accessibility, privacy, retention, observability and operational needs
when applicable. Do not assert regulatory commitments without input.

## 8. Integration & Data Requirements
| ID | Service / interface | Authentication / data contract | Failure / quota policy | Acceptance |
| --- | --- | --- | --- | --- |
| BRD-INT-001 | [Integration] | [Contract] | [Behavior] | [Verification] |

[Domain entities, relationships, persisted state, sensitivity, ownership and
lifecycle. State explicitly if no external integrations are required.]

## 9. Risks, Mitigations & Open Decisions
| ID | Risk / question | Likelihood / impact | Mitigation / decision owner | Blocking? |
| --- | --- | --- | --- | --- |
| R-001 | [Risk] | [Assessment] | [Action] | [Yes / No] |

## 10. Appendix & Traceability
[Glossary, source references, clarifications, change history and mapping from
brief sections to requirement IDs.]
