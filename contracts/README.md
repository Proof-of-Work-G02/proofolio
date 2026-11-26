# contracts

Owner: **all three teams** (Frontend, Backend, AI). Every change needs approval from each team.

Machine-readable versions of the contracts in `docs/Communication Contracts/` and
`docs/Design/Failure Handling Design.md`. The docs explain *why*; these files are what code
validates against. If a schema and a doc disagree, that is a bug: report it, don't pick one.

## Index

| Task | What | Folder | Status |
|---|---|---|---|
| KAN-6 | Queue events, the error-code enum, statuses | `schemas/events/`, `schemas/common/` | Done |
| KAN-14 | Documents: profile, extraction results, unified profile, website draft, sections, template manifest | `schemas/documents/` | Planned |
| KAN-15 | HTTP API bodies and the render-worker call | `schemas/http/` | Planned |
| KAN-7 | Validation command and generated TypeScript / Python types | tooling | Planned |

## Layout

```
contracts/
  schemas/
    common/      enums and shared field types, referenced by every other schema
    events/      one schema per queue event, named <event>.schema.json
  examples/
    <schema>.json                 a valid example, must pass
    invalid/<schema>-<case>.json  must FAIL, one file per broken rule
```

All schemas are JSON Schema **draft 2020-12**. An example's schema is the one whose name is
the longest prefix of the file name.

## Conventions

- **Fields are camelCase**, events are lowercase dot names (`cv.extract.requested`). Communication Standards §3.
- **`schemaVersion: 1`** on every event. Breaking changes raise it (see "Changing a contract").
- **No unknown fields** (`additionalProperties: false`). Communication Standards §4.2: consumers must
  not accept unknown fields unless the schema allows it. So even adding an optional field is a
  contract change that consumers pick up together.
- **Timestamps** are UTC RFC 3339 ending in `Z` (`2026-11-17T14:30:00Z`).
- **Ids are opaque strings** (`jobId`, `taskId`, ...). Never parse them. `eventId` is a UUID.
- **S3 keys are relative to their bucket**: `cvS3Key` = `user-123/job-456/cv.pdf`,
  `resultS3Key` = `job-456/task-789/cv.json`.
- **Slugs** are lowercase letters, digits and hyphens, a DNS label of at most 63 characters.
- Examples use one fictional person, **Alex Popescu** (`user-123`, `job-456`, slug `alex-popescu`),
  shared by all contract tasks and the test fixtures.

## Queue events

Flat JSON (no envelope). Common fields: `schemaVersion`, `eventId`, `event`, `occurredAt`, `jobId`.
Request events may carry `attempt`; `processing.completed` and `processing.failed` echo it so Core
can drop results from an older attempt.

| Event | Queue | Producer → consumer | Extra fields |
|---|---|---|---|
| `cv.extract.requested` | `cv-extraction` | Core → CV Extraction | `taskId`, `userId`, `cvS3Key` |
| `github.analyze.requested` | `github-analysis` | Core → GitHub Analysis | `taskId`, `userId`, `githubUsername` (no token) |
| `linkedin.extract.requested` | `linkedin-extraction` | Core → LinkedIn Extraction | `taskId`, `userId`, `linkedinS3Key` |
| `processing.completed` | `processing-results` | AI services → Core | `taskId`, `sourceType`, `status` = `COMPLETED`, `resultS3Key` |
| `processing.failed` | `processing-results` | AI services → Core | `taskId`, `userId`, `sourceType` + failure fields |
| `profile.ready` | `website-generation` | Core → Website Service | `userId`, `profileId`, `templateId` |
| `website.generated` | `processing-results` | Website Service → Core | `userId`, `profileId`, `websiteId`, `status` = `PREVIEW_READY` |
| `website.publish.requested` | `website-publishing` | Website Service outbox → Website Publisher | `userId`, `websiteId`, `slug` |
| `website.published` | `processing-results` | Website Publisher → Core | `userId`, `websiteId`, `slug`, `status` = `PUBLISHED`, `url` |
| `website.failed` | `processing-results` | Website Service → Core | `userId`, `profileId`, optional `websiteId` + failure fields |

**Failure fields** (Failure Handling Design §3.1): `stage`, `errorCode`, `errorMessage` (user-safe,
max 500 characters), `retryable`, `attempts`, optional `diagnosticsS3Key`. `processing.failed` only
takes the three extraction stages; `website.failed` only `WEBSITE_GENERATION` or `WEBSITE_PUBLISHING`.

## Error codes

One enum, `schemas/common/error-code.schema.json`, used by every event and HTTP error body.
**Nothing outside it may appear in an event or HTTP body.** Services may add a code (a contract
change) but never repurpose one.

| Code | Group | Typical `retryable` |
|---|---|---|
| `SOURCE_UNREADABLE` | Permanent | No |
| `SOURCE_NOT_FOUND` | Permanent (for example an unknown GitHub user) | No |
| `SOURCE_EMPTY` | Permanent (no usable content) | No |
| `AI_OUTPUT_INVALID` | Permanent after LLM-output retries | Yes |
| `AI_PROVIDER_UNAVAILABLE` | Transient, retries exhausted | Yes |
| `EXTERNAL_RATE_LIMITED` | Transient, retries exhausted (GitHub, LLM provider) | Yes |
| `STORAGE_ERROR` | Transient, retries exhausted | Yes |
| `INTERNAL_ERROR` | Either | Yes |
| `TIMEOUT` | Raised by the Core watchdog | Yes |
| `RETRIES_EXHAUSTED` | Raised by the Core DLQ listener | Yes |
| `SLUG_TAKEN` | Publishing: slug owned by another user | Needs a user change |
| `SLUG_CONFLICT` | HTTP only: different slug for an already published site | Needs a user change |
| `PUBLISH_ASSET_ERROR` | Publishing: render or upload failed | Yes |
| `JOB_NOT_RETRYABLE` | HTTP only: retry of a job that cannot be retried | No |
| `RATE_LIMITED` | HTTP only: request, upload or generation limit (`429`) | Yes, later |

### Mapping internal error names to the enum

Inside a service you may use more precise exception names. They are mapped **once**, here, and
only the enum value leaves the service.

| Situation inside a service | Typical internal name | Enum code |
|---|---|---|
| CV or LinkedIn PDF/DOCX is encrypted, corrupt or has no text layer | `DOCUMENT_UNREADABLE` | `SOURCE_UNREADABLE` |
| LinkedIn PDF is not a LinkedIn export | `NOT_A_LINKEDIN_PDF` | `SOURCE_UNREADABLE` |
| Document parses but holds no usable professional data | `DOCUMENT_EMPTY` | `SOURCE_EMPTY` |
| GitHub user does not exist | `GITHUB_USER_NOT_FOUND` | `SOURCE_NOT_FOUND` |
| GitHub user has no public repositories | `GITHUB_NO_PUBLIC_REPOS` | `SOURCE_EMPTY` |
| LLM output fails schema validation after its retries | `LLM_OUTPUT_INVALID` | `AI_OUTPUT_INVALID` |
| Generated website draft fails the draft or section schemas | `DRAFT_INVALID` | `AI_OUTPUT_INVALID` |
| LLM provider 5xx, overloaded or unreachable after retries | `LLM_UNAVAILABLE` | `AI_PROVIDER_UNAVAILABLE` |
| LLM provider or GitHub 429 / secondary rate limit after retries | `UPSTREAM_RATE_LIMITED` | `EXTERNAL_RATE_LIMITED` |
| S3 read or write fails after retries | `S3_ERROR` | `STORAGE_ERROR` |
| Render worker error or static-file upload fails | `RENDER_FAILED`, `UPLOAD_FAILED` | `PUBLISH_ASSET_ERROR` |
| Anything unexpected | (any unhandled exception) | `INTERNAL_ERROR` |

## Statuses

| Enum | Values | Owner |
|---|---|---|
| `job-status` | `QUEUED`, `PROCESSING`, `AGGREGATING`, `GENERATING`, `PREVIEW_READY`, `PUBLISHING`, `PUBLISHED`, `FAILED` | Core Backend |
| `task-status` | `PENDING`, `COMPLETED`, `FAILED` | Core Backend |
| `website-status` | `GENERATING`, `GENERATION_FAILED`, `PREVIEW_READY`, `PUBLISHING`, `PUBLISH_FAILED`, `PUBLISHED`, `UNPUBLISHED` | Website Service |

Allowed transitions are in Failure Handling Design §6.4. `UNPUBLISHED` is a site whose slug was
taken over by the same owner's newer site (Database Architecture §5.10).

## Changing a contract

1. Open a PR that touches **only** `contracts/` (and the matching doc in `docs/`). Never hide a contract
   change in a feature PR.
2. Update or add the valid example and at least one invalid example in the same PR.
3. Get approval from **all three teams** (CODEOWNERS lists them).
4. **Breaking change** (remove or rename a field, make an optional field required, change a type,
   remove or repurpose an enum value, tighten a pattern): raise `schemaVersion` and plan the
   consumer migration (Communication Standards §4.4). Because of `additionalProperties: false`,
   adding an optional field also needs consumers updated before producers send it.
5. Validation must pass (see KAN-7 tooling once merged).
