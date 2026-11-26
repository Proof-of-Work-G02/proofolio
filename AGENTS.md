# AGENTS.md

Instructions for AI coding agents (Claude Code, Codex, Copilot, Cursor and others) working in this repository.

## The one rule: read the docs before you write code

The design documents in `docs/` are the source of truth for how Proofolio works. Before you implement, change or review anything:

1. Find the docs that cover the area you are touching (use the map below).
2. Read the relevant sections in full. Skimming headings is not enough.
3. Check that your plan matches them: names, fields, event types, endpoints, status values, table columns, error codes, retry limits.
4. Only then write code.

If the task, the docs and the existing code disagree, **stop and say so**. Do not guess, and do not quietly pick one. Name the files and sections that conflict and ask which one is right. If you cannot ask, take the option the docs describe and write down the conflict in the pull request description.

Never invent a field, event, endpoint, status or table that the docs do not define. If something you need is missing, say what is missing and propose it as a docs change instead of hard-coding it.

## Which doc covers what

| You are working on | Read first |
| --- | --- |
| The whole system, the end-to-end flow, how the pieces fit | `docs/System Architecture – Happy Flow (v1.1).md`, `docs/High Level Architecture Diagram.png` |
| Which services exist and how they talk | `docs/Service Architecture & Communication/README.md` |
| Core Backend (auth, ingestion, job orchestration, profile aggregation) | `docs/Service Architecture & Communication/Core Backend Service.md` |
| Website Service (generator, publisher, hosting, subdomains) | `docs/Service Architecture & Communication/Website Service.md` |
| CV extraction | `docs/Service Architecture & Communication/CV Extraction Service.md` |
| LinkedIn extraction | `docs/Service Architecture & Communication/LinkedIn Extraction Service.md` |
| GitHub analysis | `docs/Service Architecture & Communication/GitHub Analysis Service.md` |
| Naming, JSON format, IDs, dates, versioning, idempotency, general HTTP rules | `docs/Communication Contracts/Communication Standards.md` |
| Public and internal REST endpoints, auth, status codes, validation | `docs/Communication Contracts/HTTP API Contracts.md` |
| SQS queues, event payloads, dead-letter queues, delivery rules | `docs/Communication Contracts/SQS Event Contracts.md` |
| Extraction results, the canonical profile, `WebsiteDraft` and other shared data shapes | `docs/Communication Contracts/Shared Data Contracts.md` |
| Tables, columns, ownership, migrations, S3 layout | `docs/Database Architecture/Database Architecture.md`, `docs/Database Architecture/Database Diagram.png` |
| Errors, retries, DLQs, job/task/website statuses and allowed transitions, duplicate events | `docs/Design/Failure Handling Design.md` |
| Website templates, template manifests, section schemas, the shared renderer | `docs/Design/Template System Spec.md` |
| Branches, PR titles, review rules | `docs/CONTRIBUTING.md` |

Most tasks touch more than one row. A new event, for example, needs the SQS Event Contracts, the Communication Standards, the Failure Handling Design and the docs of every service that sends or receives it.

## Which doc wins

- `docs/Design/` documents are newer and fill gaps in the older docs. Failure Handling Design fills the gaps left open in Communication Standards §8.7, §16.2 and §16.3, so follow it for anything about failures. Template System Spec §9 lists the changes it makes to other docs.
- The Communication Contracts docs win over individual service docs on anything that crosses a service boundary.
- `contracts/` (JSON schemas) must match the Communication Contracts docs. If they differ, report it.
- Anything still unclear: ask. Do not resolve it yourself.

## Ownership and contracts

- Each folder is owned by one team (see the table in `README.md` and `.github/CODEOWNERS`). Stay inside the folders your task is about.
- `contracts/` belongs to all three teams. A contract change goes in its own pull request and needs approval from every team. Do not slip contract changes into a feature PR.
- If your change needs a docs update, update the doc in the same PR or call it out clearly in the PR description.

## Branches and pull requests

- Never push to `main`. It is protected.
- Branch from `main` and name the branch `frontend/feature/<name>`, `backend/feature/<name>` or `ai/feature/<name>`, where `<name>` is lowercase letters, digits and dashes. Use the branch name written on the Jira task when there is one.
- Title the PR in Conventional Commits style ending with the Jira key in brackets, for example `feat(core): add job upload endpoint (BE-11)`. Allowed types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `ci`, `build`. Allowed keys: `FE-`, `BE-`, `AI-`, `KAN-`. CI rejects anything else.
- Fill in the PR template, including the acceptance criteria from the Jira task and the docs sections you followed.
- Never commit secrets, API keys or real personal data. Use `.env` (ignored) and keep `.env.example` free of real values.

## Before you open a pull request

- [ ] I read the docs for every area this change touches.
- [ ] Names, fields, events, endpoints, statuses and error codes match the docs exactly.
- [ ] Any conflict between the task, the docs and the code is written in the PR description.
- [ ] Contract changes, if any, are in their own PR.
- [ ] Branch name and PR title follow the rules above.
