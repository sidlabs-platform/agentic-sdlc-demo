# Business Requirements Document (BRD)

| Field | Value |
| --- | --- |
| Title / Version / Date | Copilot Agentic AI Academy / 1.0 / 2026-10-16 |
| Author / Review status | 1-requirement-agent / Draft for writer review; not yet accepted |
| Source brief | [Root issue #2](https://github.com/sidlabs-platform/agentic-sdlc-demo/issues/2); verbatim copy in `docs/requirements/application-brief.md` |

## 1. Executive Summary

### Project Overview

Copilot Agentic AI Academy is a self-paced web learning application for developers who are new to agentic AI and GitHub Copilot's agent capabilities. It presents five ordered lessons, lesson quizzes, a guided manual lab, and browser-local progress. Its purpose is to help learners understand safe and effective use of coding agents, including the human responsibilities in the issue-to-PR, review, and merge workflow.

### Business Objectives and Success Metrics

| KPI ID | Objective | Target | Measurement |
| --- | --- | --- | --- |
| KPI-001 | Enable completion of the full curriculum in a short self-paced session. | Full curriculum completable in under 60 minutes. | Sum the lesson and lab time estimates and verify the total is under 60 minutes. |
| KPI-002 | Teach the agent-assisted delivery loop and human responsibilities. | The five-lesson curriculum covers the issue → agent → PR → review → human merge loop and human responsibilities. | Review lesson and quiz content to confirm coverage of each stage and human responsibility. |
| KPI-003 | Retain learner progress across visits on the same device. | Lesson completion, quiz best scores, and lab step state survive a browser reload/session restart on that device. | Complete actions, reload/reopen the application, and verify the saved progress is restored. |

## 2. Background & Context

Developers new to agentic AI may not understand how coding agents fit into software delivery or how Copilot agent mode, cloud agent, custom agents, and code review relate. The brief identifies a need for concise, practical instruction that combines conceptual lessons with quizzes and a guided lab. Product details can change, so lessons should explain concepts and direct learners to official GitHub documentation for current specifics.

## 3. Stakeholders, Personas & Journeys

| Persona / stakeholder | Responsibility / need | Journey | Influence |
| --- | --- | --- | --- |
| Learner (developer) | Learn agentic AI and Copilot agent capabilities safely and effectively. | Open the catalog, complete lessons and quizzes, follow the lab checklist, and review progress. | Primary user |
| Content maintainer (repository contributor) | Keep lesson, quiz, and lab material accurate and useful without changing application code. | Edit versioned content files and submit changes through a pull request; automated validation checks content. | Owns curriculum changes |
| Repository maintainer / reviewer | Review content and application changes and ensure they meet repository quality expectations. | Review pull requests and automated checks before changes are merged. | Approves repository changes |

## 4. Scope

### In Scope

- **Must:** Static client-side learning app with an ordered five-lesson catalog, viewer, previous/next navigation, and explicit completion action.
- **Must:** Three multiple-choice questions per lesson, feedback and explanations, scoring, a 2/3 passing threshold, and retries.
- **Must:** Checkable guided lab for writing an issue, assigning Copilot, reviewing a PR, requesting changes, and manually merging; link to official GitHub documentation without automating GitHub actions.
- **Must:** Browser-local progress for lesson completion, quiz best scores, and lab steps, displayed on the catalog and a progress summary, with confirmed reset.
- **Must:** Versioned repository content and automated validation for required fields, unique IDs, and exactly one correct answer per question.
- **Must:** Keyboard-accessible access to all lessons, questions, and the lab; safe rendering of content; responsive use from 360 px mobile width through desktop.
- **Must:** Build and tests execute in CI without access to external AI or GitHub APIs.

### Out of Scope / Deferred

- User accounts, login, server-side storage, and multi-device progress synchronization.
- Runtime calls to LLMs or GitHub APIs, and live Copilot integration.
- Content authoring UI, analytics, certificates, payments, and localization.
- Deployment/hosting configuration; this run produces a build artifact suitable for static hosting.
- Framework/runtime, detailed content-file format, and safe-rendering implementation: the brief assigns these decisions to the design stage.

### Assumptions, Constraints & Dependencies

- **Confirmed constraints:** Static client-side application; no backend, secrets, API keys, tokens, or collection of personal data. Runtime integrations are absent. Progress is in browser local storage. Builds and tests run on GitHub-hosted Ubuntu runners.
- **Confirmed targets:** Under 60 minutes for the curriculum; initial page load under 2 seconds on typical broadband; shipped assets target less than 500 KB excluding images; WCAG 2.2 AA intent; mobile usability at widths of 360 px and above; support for latest Chrome, Edge, Firefox, and Safari.
- **Dependencies:** Official GitHub documentation is the source for links supporting changing product-specific details. Repository content files and their automated validation are required for maintainers to update learning material.
- **Design-stage decisions:** Framework versus plain HTML/TypeScript; content format; safe-rendering approach; and concrete validation methods for performance, asset size, and browser support. These decisions do not block documenting the business scope but must be resolved in design before implementation choices are made.
- **Interpretation:** “No personal data collected” means the application must not request or transmit learner identity or activity; the only learner state specified is progress stored locally in the browser.

## 5. Use Cases

| ID | Actors | Preconditions / flow | Outcome | Priority |
| --- | --- | --- | --- | --- |
| UC-001 | Learner | Open the application, choose one of five ordered catalog entries, read lesson content, navigate previous/next, and mark the lesson complete. | Learner can read lessons and see completion status. | Must |
| UC-002 | Learner | Answer the three multiple-choice questions for a lesson, submit, review correctness and explanations, and retry if desired. | Learner sees a score and whether the quiz passed at 2/3 or better. | Must |
| UC-003 | Learner | Follow the guided lab, check off each step, and use its official-documentation links while performing GitHub actions manually. | Lab state is visible and GitHub is not automated by the app. | Must |
| UC-004 | Learner | Complete lessons, quizzes, or lab steps; revisit the catalog or progress summary; reload the application; optionally confirm a reset. | Progress is restored locally or fully cleared after confirmed reset. | Must |
| UC-005 | Content maintainer | Edit versioned lesson, quiz, or lab files and run automated content validation through the repository workflow. | Valid content can be maintained without application-code changes; invalid content fails tests. | Must |

## 6. Functional Requirements

| ID | Requirement | Priority | Measurable acceptance criteria |
| --- | --- | --- | --- |
| BRD-FR-001 | The application shall provide a home-page catalog of five lessons in the specified order, with each lesson's title, summary, estimated minutes, and completion status. | Must | The catalog contains exactly the five topics and their ordering in the source brief; each entry displays all four required fields. |
| BRD-FR-002 | The application shall render lesson headings, paragraphs, lists, code blocks, and links, and provide previous/next navigation and a “Mark complete” action. | Must | Each supported content type renders; navigation moves between adjacent lessons; invoking “Mark complete” updates that lesson's completion status. |
| BRD-FR-003 | The application shall provide three multiple-choice questions for each of the five lessons, show per-question correctness and a short explanation after submission, display a score, pass at a score of at least 2/3, and allow retry. | Must | There are 15 questions total; tests verify scoring, feedback, the 2/3 pass boundary, and retry behavior. |
| BRD-FR-004 | The application shall provide the guided lab as a checkable sequence covering issue writing, Copilot assignment, PR review, requesting changes by comment, and manual merge. | Must | All five activities are present as checkable steps; lab links point to official GitHub documentation; no step triggers GitHub automation. |
| BRD-FR-005 | The application shall persist lesson completion, each lesson's best quiz score, and lab step state in browser-local storage and show this progress on the catalog and a progress summary. | Must | After each progress type is changed and the page is reloaded, the saved state appears in both required views; best score does not decrease after a lower retry score. |
| BRD-FR-006 | The application shall offer a “Reset progress” action that clears all saved learner progress after confirmation. | Must | Canceling confirmation leaves progress unchanged; confirming reset removes all saved lesson, quiz, and lab state. |
| BRD-FR-007 | Lesson, quiz, and lab content shall be stored in versioned repository files and validated automatically so maintainers can change content without application-code changes. | Must | Automated tests reject missing required fields, duplicate IDs, and questions with anything other than exactly one correct answer; valid content passes validation. |
| BRD-FR-008 | All lessons, all 15 questions, and the lab shall be reachable from the home page using only a keyboard. | Must | Keyboard-only navigation can reach and operate every lesson, quiz, and lab step without a pointer. |
| BRD-FR-009 | The application shall render lesson content safely without executing scripts embedded in content. | Must | A test content payload containing script markup does not execute script behavior when rendered. |
| BRD-FR-010 | The build and automated tests shall run in CI without network access to external AI or GitHub APIs. | Must | CI build and tests pass with external AI/GitHub API access unavailable; the app makes no runtime API calls to those services. |

## 7. Non-Functional Requirements

| ID | Category | Requirement / target | Verification |
| --- | --- | --- | --- |
| BRD-NFR-001 | Accessibility | Meet the brief's WCAG 2.2 AA intent through semantic HTML, keyboard navigation, visible focus, sufficient contrast, and labelled form controls. | Automated accessibility checks where supported plus manual keyboard, focus, contrast, and form-label review against the stated criteria. |
| BRD-NFR-002 | Performance / size | Initial page load under 2 seconds on a typical broadband connection; total shipped assets target less than 500 KB excluding images. | Measure initial load and shipped asset size using a repeatable method documented in design/bootstrap; report image bytes separately. |
| BRD-NFR-003 | Responsive usability | Remain usable at mobile viewport widths of 360 px and above and on desktop. | Exercise catalog, lesson, quiz, and lab at 360 px and a desktop viewport without loss of content or operation. |
| BRD-NFR-004 | Privacy | Collect no personal data; keep specified learner progress in browser-local storage, without accounts, server-side storage, or multi-device sync. | Inspect application data flows and storage; verify no identity request or transmission of learner progress. |
| BRD-NFR-005 | Security | Operate without a backend or secrets; render repository-supplied lesson content safely; remain compatible with a strict Content Security Policy; keep dependencies minimal and scanned. | Verify no backend/API credentials, test content rendering, exercise the chosen CSP, and run the selected dependency scanning gate. Exact CSP and scanning tools are design/bootstrap decisions. |
| BRD-NFR-006 | Browser compatibility | Support latest Chrome, Edge, Firefox, and Safari. | Verify the application in the latest stable release of each named browser at release time; record versions in test evidence. |
| BRD-NFR-007 | Quality / maintainability | Provide automated unit tests for quiz logic, progress storage, and content validation; lint and type-check where supported by the selected stack. | CI executes those tests; design documents the selected stack and corresponding lint/type-check commands or their applicability. |
| BRD-NFR-008 | Content accuracy | Explain Copilot features conceptually and link to official docs.github.com pages for changing product details. | Review lesson claims and verify relevant documentation links use the official docs.github.com domain. |
| BRD-NFR-009 | Compatibility / operation | Produce static output suitable for a static host; deployment is not part of this run. | Build output consists of static-hostable assets; no deployment is required for acceptance. |

## 8. Integration & Data Requirements

| ID | Service / interface | Authentication / data contract | Failure / quota policy | Acceptance |
| --- | --- | --- | --- | --- |
| BRD-INT-001 | Runtime integrations: none. Outbound links in lessons/lab go to official GitHub documentation. | No authentication, API calls, or data exchange. A link navigates the learner to its documented HTTPS URL; no learner state is sent. | External documentation availability is outside the app's control; link failure must not prevent use of local lesson, quiz, or lab content. No API quota applies. | Inspect network activity to confirm there are no runtime AI/GitHub API calls; verify content links target official documentation. |

### Data entities, persisted state, sensitivity, ownership, and lifecycle

| Entity / state | Source and owner | Persistence and sensitivity | Lifecycle |
| --- | --- | --- | --- |
| Lesson content | Versioned repository files; maintained by repository contributors through pull requests. | Static public learning material; not learner-specific. | Reviewed and validated on content changes. |
| Quiz content | Versioned repository files; maintained by repository contributors through pull requests. | Static public questions, answer keys, and explanations. | Automated validation requires complete fields, unique IDs, and exactly one correct answer per question. |
| Lab content | Versioned repository files; maintained by repository contributors through pull requests. | Static instructions and official documentation links. | Reviewed and validated on content changes. |
| Learner progress | Generated in the browser by learner actions. | Browser local storage on the same device; no identity or server-side copy. | Persists across browser sessions until learner confirms reset or browser storage is otherwise cleared. |

## 9. Risks, Mitigations & Open Decisions

| ID | Risk / question | Likelihood / impact | Mitigation / decision owner | Blocking? |
| --- | --- | --- | --- | --- |
| R-001 | Copilot product details may change and make lessons stale. | Medium / Medium | Keep explanations conceptual, link to official documentation, and maintain content through reviewed pull requests. Content maintainer. | No |
| R-002 | Browser-local storage may be unavailable or cleared, losing progress. | Medium / Low | Keep the data limited to the specified same-device progress and disclose the local-only persistence model; the brief does not specify behavior when browser storage is unavailable. Design/implementation. | No |
| R-003 | Content-format and rendering choices may create unsafe rendering or overly complex maintenance. | Medium / High | Design stage chooses a content format and safe-rendering strategy; tests verify embedded scripts do not execute. Design owner. | No; required before implementation design is finalized |
| R-004 | “Typical broadband” and “latest stable” are not fixed test environments, and the brief does not specify detailed measurement conditions. | Medium / Medium | Design/bootstrap documents repeatable load/asset measurement conditions and browser versions used for verification without changing the stated targets. Design/bootstrap owner. | No |
| R-005 | The brief leaves framework versus plain HTML/TypeScript and content format open. | Low / Medium | Design agent evaluates options for simplicity and testability and records the justified stack and content-format decision. Design owner. | No; explicitly deferred to design |

## 10. Appendix & Traceability

### Glossary

- **Agentic AI:** AI systems described in the curriculum as agents with tools, planning, and varying autonomy levels.
- **Learner:** Developer using the application to learn agentic AI and GitHub Copilot agent capabilities.
- **Content maintainer:** Repository contributor who updates versioned lesson, quiz, or lab content through pull requests.
- **Guided lab:** Checkable learning steps that direct learners to perform GitHub work manually.

### Source references

- Root application brief: [sidlabs-platform/agentic-sdlc-demo#2](https://github.com/sidlabs-platform/agentic-sdlc-demo/issues/2), captured verbatim in `docs/requirements/application-brief.md` on 2026-10-16 (UTC).
- GitHub Copilot coding agent: https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent
- Using the coding agent: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent
- Copilot code review: https://docs.github.com/en/copilot/concepts/agents/code-review
- Risks and mitigations: https://docs.github.com/en/copilot/concepts/security-governance-and-network-settings/risks-and-mitigations

### Brief-to-requirement traceability

| Brief section | BRD coverage |
| --- | --- |
| Problem, users, desired outcomes | Sections 1–3; KPI-001–KPI-003 |
| Six MVP capabilities | BRD-FR-001–BRD-FR-007; UC-001–UC-005 |
| Acceptance criteria | BRD-FR-003, BRD-FR-005–BRD-FR-010; BRD-NFR-001–BRD-NFR-009 |
| Out of scope | Section 4, “Out of Scope / Deferred” |
| Constraints and non-functional requirements | BRD-NFR-001–BRD-NFR-009; Section 4, “Assumptions, Constraints & Dependencies” |
| Data, integrations, and operating environment | BRD-INT-001; Section 8 data table; BRD-NFR-006 and BRD-NFR-009 |
| Open decisions and references | R-003–R-005; source references above |

### Clarifications and change history

- 2026-10-16: Initial draft derived from root issue #2. No later clarifications were available at capture time. Framework and content format remain assigned to design as directed by the brief.
