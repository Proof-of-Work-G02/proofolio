# contracts

Owner: **all three teams** (Frontend, Backend, AI). Every change needs approval from each team.

Machine-readable versions of the contracts in `docs/Communication Contracts/` and
`docs/Design/Failure Handling Design.md`. The docs explain *why*; these files are what code
validates against. If a schema and a doc disagree, that is a bug: report it, don't pick one.

## Index

| Task | What | Folder | Status |
|---|---|---|---|
| KAN-6 | Queue events, the error-code enum, statuses | `schemas/events/`, `schemas/common/` | Done |
| KAN-14 | Documents: profile, extraction results, unified profile, website draft, sections, template manifest | `schemas/profile/`, `schemas/extraction/`, `schemas/website/` | Done |
| KAN-15 | HTTP API bodies, OpenAPI, the render-worker call, HMAC test vectors | `schemas/http/`, `openapi/`, `hmac/` | Done |
| KAN-7 | Validation command, generated TypeScript / Python types, breaking-change check | `tooling/` | Done |

## Layout

```
contracts/
  schemas/
    common/      enums and shared field types, referenced by every other schema
    events/      one schema per queue event, named <event>.schema.json
    profile/     professional-profile (shared by CV and LinkedIn), unified-profile
    extraction/  cv-result, linkedin-result, github-result (files in the extraction-results bucket)
    website/     website-draft, template-manifest, sections/<type>.schema.json
    http/        HTTP request and response bodies, the render-worker call
  openapi/       OpenAPI 3.1: core-api (public /api), website-internal-api (/internal), render-worker-api
  hmac/          test vectors for service-to-service request signing
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

## Documents

JSON documents stored in S3 or Postgres and exchanged between services (Shared Data Contracts
§3–§9, Template System Spec §4–§5). Every document carries `schemaVersion: 1`.

| Schema | Title (generated type) | Producer → consumer | Stored in |
|---|---|---|---|
| `profile/professional-profile` | `CanonicalProfessionalProfile` | embedded in the results and the unified profile | |
| `extraction/cv-result` | `CVExtractionResult` | CV Extraction → Core | `extraction-results/<jobId>/<taskId>/cv.json` |
| `extraction/linkedin-result` | `LinkedInExtractionResult` | LinkedIn Extraction → Core | `extraction-results/<jobId>/<taskId>/linkedin.json` |
| `extraction/github-result` | `GitHubAnalysisResult` | GitHub Analysis → Core | `extraction-results/<jobId>/<taskId>/github.json` |
| `profile/unified-profile` | `UnifiedProfile` | Core aggregation → Website Service | `profiles.profile_data` (JSONB) |
| `website/website-draft` | `WebsiteDraft` | Website Generator → Core, Frontend, Publisher | `websites.draft_content` (JSONB) |
| `website/sections/*` | `HeroSectionData` ... `ContactSectionData` | inside a draft section's `data` | |
| `website/template-manifest` | `TemplateManifest` | template package → Generator, Core, renderer | `packages/templates/<id>/template.json` |

Rules worth knowing:

- **Profile fields are all optional.** Omit what is unknown and never invent it. An empty array
  means "known to be empty" (Shared Data Contracts §4.8). Each list item needs at least one field.
- **Dates keep the source precision**: `YYYY`, `YYYY-MM` or `YYYY-MM-DD`.
- **GitHub technologies** are `OBSERVED` or `INFERRED` and always carry at least one evidence entry.
- **The unified profile** lists in `sourceTypes` only the sources that completed, always including
  `CV`. Table-column ids (job, user, profile) are not repeated inside it, and warnings live in `jobs.warnings`.
  `provenance[].path` is a JSON Pointer into the stored document (`/profile/skills/3`).
- **A draft section** is `{id, type, data}`. `data` must match the schema of its `type`. Sections the
  profile has no data for are left out, not emitted empty. Text is plain text (the renderer escapes
  it), URLs are `https://`. Section ids must be unique within a draft; JSON Schema cannot check that,
  so the generator does.
- **Draft ids are informational**: the `websites` columns (`template_id`, `template_version`,
  `status`) are authoritative.

**Fixture set.** The valid examples describe one fictional person, Alex Popescu, consistently across
CV result, LinkedIn result, GitHub result, unified profile and website draft (job `job-456`, tasks
`task-789` CV, `task-790` GitHub, `task-791` LinkedIn, GitHub user `alex-popescu-dev`, template
`classic`). AI-8, FE-28 and the end-to-end test reuse them.

## HTTP API

Bodies are JSON Schemas in `schemas/http/`; the endpoints, status codes and headers are in the
OpenAPI 3.1 files in `openapi/`, which reference those schemas (HTTP API Contracts, Template
System Spec §6–§7).

| Endpoint | Request | Success | Errors (all `ErrorResponse`) |
|---|---|---|---|
| `POST /api/jobs` | multipart: `cv`, `templateId`, optional `githubUsername`, `linkedinPdf` | `202 CreateJobResponse` | 400, 401, 403, 413, 415, 422, 429 |
| `GET /api/jobs/{jobId}` | | `200 JobStatusResponse` | 401, 404 |
| `POST /api/jobs/{jobId}/retry` | no body | `202 JobStatusResponse` | 409 `JOB_NOT_RETRYABLE` |
| `GET /api/templates` | | `200 TemplateListResponse` | 401 |
| `GET /api/websites` | | `200 WebsiteListResponse` | 401 |
| `GET /api/websites/{id}/preview` | | `200 WebsitePreview` | 404, 409 `NOT_READY` |
| `POST /api/websites/{id}/publish` | `PublishRequest` | `202 PublishResponse` (`PUBLISHING`), `200` once `PUBLISHED` | 409 `SLUG_TAKEN` / `SLUG_CONFLICT`, 422 |
| `GET /internal/websites/{id}/preview` | signed | `200 WebsitePreview` | |
| `POST /internal/websites/{id}/publish` | signed, `PublishRequest` | `202`/`200 PublishResponse` | 409 |
| `POST /internal/websites/{id}/retry-generation` | signed | `200`, no body | 409 `JOB_NOT_RETRYABLE` |
| `POST /render` (render worker) | signed, `RenderRequest` | `200 RenderResponse` + `X-Renderer-Version` | 404, 413, 422, 500 `PUBLISH_ASSET_ERROR` |

- **Errors** are always `{ "error": { "code", "message", "requestId", "details"? } }`; `details` only
  for `422`. Clients branch on `code`, never on `message`.
- **`JobStatusResponse`**: `warnings` is always present; `error {code, message, stage, retryable}`
  when `FAILED`; `websiteId`, `slug`, `url` once `PUBLISHED` (enforced by the schema).
- **`WebsitePreview`** is flat: the draft's `schemaVersion` and `content` next to `websiteId`,
  `profileId`, `templateId`, `templateVersion`, `status` from the `websites` columns. Never a nested `draft`.
- **Render worker**: request and response must each stay under **6 MB** (AWS Lambda payload limit);
  a larger site fails with `500 PUBLISH_ASSET_ERROR`. File paths are relative, without `..`; content is
  base64. On AWS the same JSON is the Lambda payload and the call uses IAM instead of HMAC.

## Service-to-service signing (HMAC)

Used in local HTTP mode for Core → Website Service (`/internal/*`) and Website Publisher → render
worker (`/render`). Secret: `INTERNAL_SERVICE_SECRET` (`.env.example`).

```
canonical = METHOD + "
" + PATH_WITH_QUERY + "
" + X-Service-Timestamp + "
"
          + X-Actor-User-Id (empty string if absent) + "
" + hex(SHA-256(raw body bytes))
X-Service-Signature: v1=<hex(HMAC-SHA256(secret, canonical))>
```

- `X-Service-Timestamp` is Unix time in seconds. Reject when it differs from now by more than
  **60 seconds** (either way).
- Compare signatures in constant time.
- `X-Actor-User-Id` is part of the signed string, so it cannot be swapped after signing.

`hmac/test-vectors.json` holds valid, tampered-body, tampered-actor, expired, future and
wrong-secret cases with their canonical strings. The validator re-verifies them on every run; the
Python verifier (BE-10) and the Node verifier (FE-33) must pass the same vectors.

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
| `BAD_REQUEST` | HTTP only: `400` malformed request, unknown `templateId` | No |
| `UNAUTHENTICATED` | HTTP only: `401` no or expired session, bad service signature | Sign in again |
| `FORBIDDEN` | HTTP only: `403` | No |
| `CSRF_INVALID` | HTTP only: `403` missing or wrong `X-CSRF-Token` | Reload |
| `NOT_FOUND` | HTTP only: `404`, also for another user's resource (ids cannot be probed) | No |
| `NOT_READY` | HTTP only: `409` preview requested before a draft exists | Yes, later |
| `FILE_TOO_LARGE` | HTTP only: `413` upload or render request over the limit | Needs a user change |
| `UNSUPPORTED_FILE_TYPE` | HTTP only: `415` | Needs a user change |
| `VALIDATION_ERROR` | HTTP only: `422` invalid field values, with `details[]` | Needs a user change |
| `SERVICE_UNAVAILABLE` | HTTP only: `503` | Yes, later |

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
5. Run `make contracts-check` (validation, regenerated types, type smoke test) and commit the
   regenerated types. CI runs the same, plus `make contracts-breaking` against `main`.

## Tooling (KAN-7)

Needs Node 20+ and Python 3.12+. No Docker. On Windows use `python scripts/dev.py <target>`
instead of `make <target>`.

| Command | What it does |
|---|---|
| `make contracts-setup` | Installs the tooling once: `npm ci` in `contracts/tooling` and a Python venv with `datamodel-code-generator` |
| `make contracts-validate` | Every schema compiles (ajv, strict, draft 2020-12); every `examples/<schema>.json` passes; every `examples/invalid/<schema>-<case>.json` fails |
| `make contracts-types` | Regenerates the TypeScript and Python types. Commit the result |
| `make contracts-check` | Validate, then fail if the committed types are stale, then type-check every valid example against the generated types |
| `make contracts-breaking` | Compares the schemas with `origin/main` (or `--base <ref>`): fails on a removed field, a newly required field, a changed type, a removed enum value, a changed const or `$ref`, a tightened limit or pattern, or a deleted schema, unless that schema's `schemaVersion` went up |

## Using the generated types

The types are generated from the schemas and committed. **Never edit them by hand.**

**TypeScript** (`packages/contract-types-ts`, types only):

```ts
import type { CvExtractRequested, ErrorCode } from "@proofolio/contract-types";
```

**Python** (`services/_shared/python/proofolio_contracts`, Pydantic v2 models; install with
`pip install -e services/_shared/python`):

```python
from proofolio_contracts import CvExtractRequested, ErrorCode, ValidationError

event = CvExtractRequested.model_validate_json(message_body)
```

Field names stay camelCase, exactly as on the wire. The generated types are for typing and
parsing. Pydantic cannot express a few schema rules (the `Z` suffix on timestamps, the
`https://` prefix on URLs, "at least one field" on contact and profile items), so a consumer
that must enforce the whole contract validates against the JSON Schema itself (ajv in Node,
`jsonschema` in Python).
