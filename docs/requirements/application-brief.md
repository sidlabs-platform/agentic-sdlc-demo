# Application Brief

| Field | Value |
| --- | --- |
| Source | [sidlabs-platform/agentic-sdlc-demo#2](https://github.com/sidlabs-platform/agentic-sdlc-demo/issues/2) |
| Captured | 2026-10-16 (UTC) |

## Verbatim root issue description

### Problem, users and desired outcomes

Developers new to agentic AI struggle to understand how AI coding agents fit into real software delivery, and in particular how GitHub Copilot's agent capabilities (Copilot cloud agent, custom agents, Copilot code review, agent mode in the IDE) work together.

**Copilot Agentic AI Academy** is a small, self-paced learning web app that teaches these concepts through short lessons, quizzes and a guided hands-on lab.

Users:
- **Learner** – a developer who wants to understand agentic AI concepts and how to use GitHub Copilot agents safely and effectively.
- **Content maintainer** – a repository contributor who edits lesson and quiz content through pull requests.

Desired outcomes:
- A learner can complete the full curriculum in under 60 minutes.
- After completing it, a learner can explain the issue → agent → PR → review → human merge loop and the human responsibilities in it.
- Learner progress persists across browser sessions on the same device.

### Scope and acceptance criteria

Must have (MVP):
1. **Lesson catalog** – home page lists 5 lessons in order with title, summary, estimated minutes and completion status:
   1. What is agentic AI (agents vs. assistants, tools, planning, autonomy levels)
   2. GitHub Copilot agent capabilities (agent mode, cloud agent, custom agents, code review)
   3. Writing good issues and instructions for agents (scoping, acceptance criteria, `copilot-instructions.md`, custom agent profiles)
   4. Reviewing and governing agent work (PR review, CI gates, code scanning, branch rules, human merge)
   5. Safety and trust boundaries (prompt injection, secrets, least privilege, approvals)
2. **Lesson viewer** – renders lesson content (headings, paragraphs, lists, code blocks, links) with previous/next navigation and a "Mark complete" action.
3. **Quizzes** – each lesson has 3 multiple-choice questions (15 total). Learner submits answers and sees correct/incorrect per question with a short explanation. Score is shown; a lesson quiz passes at ≥ 2/3 and can be retried.
4. **Guided lab** – a step-by-step checklist walking a learner through: writing a well-scoped issue, assigning it to Copilot, reviewing the resulting PR, requesting changes with a comment, and merging manually. Steps are checkable; the lab links to official GitHub documentation rather than automating anything against GitHub.
5. **Progress tracking** – lesson completion, quiz best scores and lab step state are stored locally in the browser and shown on the catalog and a progress summary. A "Reset progress" action clears it after confirmation.
6. **Content as data** – lesson, quiz and lab content lives in versioned files in the repository (e.g. Markdown/JSON), validated by automated tests, so maintainers change content through PRs without code changes.

Acceptance criteria:
- All 5 lessons, 15 questions and the lab are reachable from the home page using only the keyboard.
- Quiz scoring, pass threshold and retry behaviour are covered by automated tests.
- Progress survives a page reload and is fully cleared by "Reset progress".
- Invalid content files (missing fields, a question without exactly one correct answer, duplicate IDs) fail the automated test suite.
- The app builds and its tests run in CI with no network access to external AI or GitHub APIs.

Out of scope:
- User accounts, login, server-side storage or multi-device sync.
- Calling any LLM or GitHub API from the app; no live Copilot integration.
- Content authoring UI, analytics, certificates, payments, localisation.

### Constraints and non-functional requirements

- **No backend and no secrets**: a static, client-side web app; no API keys, tokens or personal data collected.
- **Accessibility**: WCAG 2.2 AA intent – semantic HTML, keyboard navigation, visible focus, sufficient contrast, labelled form controls.
- **Performance**: initial page load under 2 seconds on a typical broadband connection; total shipped assets reasonably small (target < 500 KB excluding images).
- **Responsive**: usable on mobile (≥ 360 px wide) and desktop.
- **Security**: lesson content rendered safely (no execution of scripts embedded in content); strict Content Security Policy compatible; dependencies kept minimal and scanned.
- **Quality**: automated unit tests for quiz logic, progress storage and content validation; linting and type checking where the chosen stack supports it.
- **Accuracy**: content describes GitHub Copilot features at a conceptual level and links to official docs.github.com pages for details, since product specifics change.
- **Maintainability**: simple, widely used stack that Copilot agents and new contributors can work in easily; the design stage should choose and justify it.

### Data, integrations and operating environment

- Data: static content files in the repository; learner progress only in browser local storage. No server-side data.
- Integrations: none at runtime. Outbound links only to official GitHub documentation.
- Environment: modern evergreen browsers (latest Chrome, Edge, Firefox, Safari). Builds and tests run on GitHub-hosted Ubuntu runners.
- Hosting: static output suitable for any static host (e.g. GitHub Pages). Deployment is not part of this run; the build artifact is enough.

### Open decisions and references

- Front-end framework vs. plain HTML/TypeScript: decide in design, favouring simplicity and testability.
- Content format (Markdown with front matter vs. JSON) and the safe rendering approach.
- References:
  - https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent
  - https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent
  - https://docs.github.com/en/copilot/concepts/agents/code-review
  - https://docs.github.com/en/copilot/concepts/security-governance-and-network-settings/risks-and-mitigations

## Clarifications

None recorded at capture time. The stack and content-format choices above remain explicitly deferred to the design stage.
