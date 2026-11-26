# Reconciliation Change Log

Reconciles the per-service docs and the database doc with the Communication Contracts (SQS Event Contracts, Shared Data Contracts, HTTP API Contracts, Communication Standards). Where they differ, the contracts win, since they are newer. Originals are untouched; every reconciled draft sits next to its original with `(reconciled)` in the name.

Total edits: 72 in round 1 and 71 in round 2. **GUESS** marks a decision that was not in any source document.

## Files produced

**Round 2 (contracts and failure handling)**

- `Communication Contracts/Shared Data Contracts (reconciled).md`
- `Communication Contracts/SQS Event Contracts (reconciled).md`
- `Communication Contracts/HTTP API Contracts (reconciled).md`
- `Communication Contracts/Communication Standards (reconciled).md`
- The five service drafts and the database draft below were edited again in place.

**Round 1**

- `Service Architecture & Communication/CV Extraction Service (reconciled).md`
- `Service Architecture & Communication/LinkedIn Extraction Service (reconciled).md`
- `Service Architecture & Communication/GitHub Analysis Service (reconciled).md`
- `Service Architecture & Communication/Website Service (reconciled).md`
- `Service Architecture & Communication/Core Backend Service (reconciled).md`
- `Database Archictecture/Database Architecture (reconciled).md` (includes the full Mermaid ER diagram)
- `Database Diagram (reconciled).md` (the same diagram on its own, since the PNG cannot be edited here)

## Every change, by file

### CV Extraction Service (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | Header note | Reconciled | Replaced the 'preliminary definitions' note with a pointer to the contracts. |
| 2 | 2.1 Inputs | Reconciled | Input is the `cvS3Key` from the event (object key relative to the uploads bucket); added `userId`. |
| 3 | 2.2 Information categories | Reconciled | Mapped categories to canonical profile field names; added optional headline/summary/volunteering/awards rows that the canonical profile allows. |
| 4 | 2.2 Information categories | GUESS | GUESS: CV extractor may also fill `volunteering` and `awards`, which the canonical profile allows but the original CV doc did not list. |
| 5 | 2.2 Schema pointer | Reconciled | Replaced 'will be defined in the shared data contracts' with the concrete contract reference. |
| 6 | 5.2 Structured Extraction Results | Reconciled | Replaced the conceptual `personalInfo` example with the `CVExtractionResult` contract example (flat `profile`, common fields, date fields). |
| 7 | 5.2 Result reference | Reconciled | Stated that `resultS3Key` is relative to the extraction-results bucket. |
| 8 | 5.2 Contract finalized | Reconciled | Replaced 'will be finalized during API & Event Contracts phase'. |
| 9 | 6.1 cv.extract.requested payload | Reconciled | Added `schemaVersion`, `eventId`, `occurredAt` to the example payload. |
| 10 | 6.1 note | Reconciled | Added a note about the common metadata. |
| 11 | 6.2 processing.completed payload | Reconciled | Added `schemaVersion`, `eventId`, `occurredAt` to the example payload. |
| 12 | 6.2 note | Reconciled | Added a note about metadata and the store-before-publish rule. |
| 13 | 8 Architectural Notes | Reconciled | Named the shared schema instead of a generic 'shared JSON schema'. |

### LinkedIn Extraction Service (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | Header note | Reconciled | Replaced the 'preliminary definitions' note with a pointer to the contracts. |
| 2 | 2.1 Inputs | Reconciled | Input is `linkedinS3Key`; added `userId`. |
| 3 | 2.2 Information categories | Reconciled | Mapped every category to its canonical profile field (`about` -> `summary`, achievements -> `awards`, profile URL -> `links`). |
| 4 | 5.2 Structured Extraction Results | Reconciled | Replaced the conceptual `about` / `experience` example with the `LinkedInExtractionResult` contract example and field-mapping table. |
| 5 | 5.3 Result reference | Reconciled | Stated that `resultS3Key` is relative to the extraction-results bucket. |
| 6 | 6.1 linkedin.extract.requested payload | Reconciled | Added `schemaVersion`, `eventId`, `occurredAt` to the example payload. |
| 7 | 6.1 note | Reconciled | Added a note about metadata and PDF-only input. |
| 8 | 6.2 processing.completed payload | Reconciled | Added `schemaVersion`, `eventId`, `occurredAt` to the example payload. |
| 9 | 6.2 note | Reconciled | Added a note about metadata and the store-before-publish rule. |
| 10 | 8 Architectural Notes | Reconciled | Replaced vague 'represented according to the agreed schema' with the contract rule. |
| 11 | 8 Architectural Notes | Reconciled | Named the shared schema. |

### GitHub Analysis Service (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | Header note | Reconciled | Replaced the 'preliminary definitions' note with a pointer to the contracts. |
| 2 | 2.1 Responsibilities | Reconciled | The service receives a normalized `githubUsername`, not a free-form profile URL. |
| 3 | 2.1 Inputs | Reconciled | Input is `githubUsername`; added `userId`. |
| 4 | 2.2 Responsibilities | Reconciled | Tied 'confirmed vs inferred' to the `certainty` values. |
| 5 | 2.2 Information categories | Reconciled | Removed `visibility` (not in the schema; MVP analyses public repositories only). |
| 6 | 2.2 Information categories | Reconciled | Named the evidence kinds. |
| 7 | 3 Communication flow | Reconciled | Core Backend validates **and normalizes** the GitHub input. |
| 8 | 5.2 Structured Analysis Results | Reconciled | Replaced the conceptual example (plain-string technologies, no common fields) with the `GitHubAnalysisResult` contract example. |
| 9 | 5.3 Result reference | Reconciled | Stated that `resultS3Key` is relative to the extraction-results bucket. |
| 10 | 6.1 github.analyze.requested payload | Reconciled | Added `schemaVersion`, `eventId`, `occurredAt` to the example payload. |
| 11 | 6.1 note | Reconciled | Added a note about metadata. |
| 12 | 6.2 processing.completed payload | Reconciled | Added `schemaVersion`, `eventId`, `occurredAt` to the example payload. |
| 13 | 6.2 note | Reconciled | Added a note about metadata and the store-before-publish rule. |
| 14 | 8 Architectural Notes | Reconciled | Extraction schema is now defined; only the GitHub auth approach remains open. |

### Website Service (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | Header note | Reconciled | Replaced the 'preliminary definitions' note with a pointer to the contracts. |
| 2 | 5.1 websites table | Reconciled | `draft_content` follows the `WebsiteDraft` schema; stated the status vocabulary that is actually defined. |
| 3 | 5.1 websites table | Reconciled | Marked `draft_content` as the full `WebsiteDraft`. |
| 4 | 5.1 Slug constraints | GUESS | Added a note about the open status vocabulary and the draft duplication question. |
| 5 | 6.1 profile.ready | Reconciled | Added the `profile.ready` payload. |
| 6 | 6.2 website.generated | Reconciled | Added the `website.generated` payload. |
| 7 | 6.2 website.published payload | Reconciled | `website.published` now has the common metadata plus `jobId`, `userId` and `slug`. |
| 8 | 6.3 Preview | Reconciled | Preview returns a `WebsiteDraft`. |
| 9 | 6.3 Publish success | Reconciled | Added the success response body and idempotency rule. |
| 10 | 6.3 Slug conflict | Reconciled | Added the `SLUG_TAKEN` error body. |
| 11 | 6.3 Security | Reconciled | Added the proposed `X-Actor-User-Id` convention for forwarding the acting user. |
| 12 | 8 Architectural Notes | Reconciled | Pointed to the contracts instead of 'Technical Design'. |

### Core Backend Service (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | Header note | Reconciled | Replaced the 'preliminary definitions' note with a pointer to the contracts. |
| 2 | 2.2 Ingestion responsibilities | Reconciled | GitHub input is normalized to `githubUsername`. |
| 3 | 2.2 Ingestion responsibilities | Reconciled | LinkedIn input is the exported PDF (`linkedinPdf`), as in the HTTP contract and ADR-009. |
| 4 | 2.2 Ingestion inputs | Reconciled | LinkedIn input renamed. |
| 5 | 2.3 Job Orchestration responsibilities | Reconciled | Stored result reference is `resultS3Key`, optionally with a JSONB copy. |
| 6 | 5.1 jobs table | Reconciled | Listed the job statuses defined in the HTTP API Contracts. |
| 7 | 5.1 job_tasks table | Reconciled | Listed task statuses and flagged the guessed ones. |
| 8 | 5.1 extraction_results table | Reconciled | Added the `result_s3_key` column and made `result_data` a nullable JSONB copy (recommended MVP approach in the Database Architecture). |
| 9 | 5.1 extraction_results table | GUESS | GUESS: `result_s3_key` is NOT NULL and `result_data` nullable. |
| 10 | 5.1 profiles table | Reconciled | `profile_data` follows `UnifiedProfile`; noted `UNIQUE(job_id)` and the `user_id` column. |
| 11 | 5.2 S3 structure | Reconciled | LinkedIn file name is `linkedin-profile.pdf`, as in SQS Event Contracts and the LinkedIn doc. |
| 12 | 6.2 Event payload summary | Reconciled | Added an event payload summary table with common metadata and business fields for every event. |
| 13 | 6.3 HTTP endpoints intro | Reconciled | Routes and bodies are defined in HTTP API Contracts; only the auth mechanism is open. |
| 14 | 6.3 POST /api/jobs | Reconciled | Documented the multipart fields and the 202 response. |
| 15 | 6.3 POST publish | Reconciled | Documented the request body and idempotency. |

### Database Architecture (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | 3.1 High-Level Database Diagram | Reconciled | Kept the PNG, added a note listing every missing column/relationship and a full Mermaid ER diagram with all columns and unique markers. |
| 2 | 3.1 oauth_accounts.created_at | GUESS | GUESS: `created_at` on `oauth_accounts` appears only in the reconciled diagram (not in the original tables). |
| 3 | 5.4 Jobs status | Reconciled | Listed the job statuses already used in HTTP API Contracts as the working set. |
| 4 | 5.6 extraction_results table | Reconciled | Added `result_s3_key` row and `result_data` is now an optional JSONB copy. |
| 5 | 5.6 recommended approach | Reconciled | Made the recommended approach concrete. |
| 6 | 5.7 profiles | Reconciled | Noted how the IDs inside `UnifiedProfile` relate to the table columns. |
| 7 | 7.2 Foreign keys | Reconciled | Added the two foreign keys missing from the list (`profiles.user_id`, `websites.user_id`). |

## Checked and left unchanged

- `System Architecture – Happy Flow (v1.1).md` and `High Level Architecture Diagram.png`: consistent with the contracts (five queues, seven events, PDF-only LinkedIn, one bucket and CloudFront distribution). Not edited.
- The four original contract documents and `Failure Handling Design.md` are not edited. Round 2 produced reconciled copies of the contracts (see below).

## Decisions (approved by the user, 2026-11-26)

- Status lists follow `Failure Handling Design.md`: job gains `PUBLISHING`; task is `PENDING` / `COMPLETED` / `FAILED` with no `PROCESSING`; website is `GENERATING`, `GENERATION_FAILED`, `PREVIEW_READY`, `PUBLISHING`, `PUBLISH_FAILED`, `PUBLISHED`. Only the status lists were copied into the drafts, not the new columns or the `processing.failed` / `website.failed` events.
- `extraction_results`: `result_s3_key` required, `result_data` optional JSONB copy.
- Table columns are the single source for ids: `profiles.profile_data` does not repeat `profileId`, `jobId`, `userId`, and `websites.draft_content` holds only the draft `content`.

## Remaining guesses

1. The CV extractor may also fill `volunteering` and `awards`.
2. `oauth_accounts.created_at` appears only in the Mermaid diagram.
3. The event IDs and timestamps added to the LinkedIn and GitHub `processing.completed` examples are invented sample values.

## Round 2: contracts and failure handling

71 edits. Source: `Failure Handling Design.md` v1.0 §11 and the accepted decision that table columns are the single source for ids. Failure-design numbers (retry counts, timeouts, thresholds, lease length) remain starting values marked GUESS in that design.

Extra guesses introduced in this round:

- `WebsitePreview` is a flat object (draft fields plus `websiteId`, `profileId`, `templateId`, `status`).
- Route name `POST /internal/websites/{websiteId}/retry-generation`, error code `JOB_NOT_RETRYABLE`, and HTTP `500` for a failed publish.
- `outbox` and `dlq_seen` column names; the failure-handling column names are taken from the source design.
- Core moves the job to `PUBLISHING` when it forwards a publish request.
- One consequence of `UNIQUE(websites.profile_id)`: a profile now has at most one website, so another template needs a new job (the database draft now says so).

### Shared Data Contracts (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | Header | Reconciled | Added a note that this is a reconciled copy. |
| 2 | 3.3 / 3.4 (new) | Reconciled | Added `FailureInfo` shape, the error code enum and the `JobWarning` shape (Failure Handling Design §3.1, §3.4, §6.5). |
| 3 | 8.2 UnifiedProfile example | Reconciled | Removed `profileId`, `jobId` and `userId` from the stored JSON; they are the `profiles.id`, `job_id` and `user_id` columns. |
| 4 | 8.3 UnifiedProfile fields | Reconciled | Removed the `profileId`, `jobId` and `userId` rows and added a note that the columns are authoritative. |
| 5 | 8.3 note | Reconciled | Stated that ids live only in the table columns (decision accepted 2026-11-26). |
| 6 | 9.2 WebsiteDraft example | Reconciled | Removed `websiteId`, `profileId`, `templateId` and `status` from the stored draft JSON; they are `websites` columns. |
| 7 | 9.3 WebsiteDraft fields | Reconciled | Removed the id, template and status rows from the draft fields table. |
| 8 | 9.3 note | GUESS | Defined the `WebsitePreview` response, which adds the column values to the draft (GUESS: exact shape). |
| 9 | 2.2 Registry / 9.1 / 9.6 | Reconciled | The preview endpoints return `WebsitePreview`, not the stored draft. |

### SQS Event Contracts (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | Header | Reconciled | Added a note that this is a reconciled copy. |
| 2 | 2.1.1 Dead-Letter Queues (new) | Reconciled | Added the five DLQs with visibility timeout, `maxReceiveCount` and retention, plus the DLQ listener rule. |
| 3 | 2.2 Event Registry | Reconciled | Seven events became nine. |
| 4 | 2.2 Event Registry | Reconciled | Added `processing.failed` and `website.failed` rows. |
| 5 | 3.1 Common fields | Reconciled | Added the optional `attempt` field. |
| 6 | 5.1 Consumer responsibilities | Reconciled | Step 8 checks for terminal tasks, not only completed ones. |
| 7 | 5.1 Aggregation rule | Reconciled | Aggregation starts when all requested tasks are terminal and the CV is `COMPLETED`; failed optional sources become warnings. |
| 8 | 5.2 processing.failed (new) | Reconciled | Added the `processing.failed` event (contract, example, producer and consumer rules). |
| 9 | 6.1 profile.ready idempotency | Reconciled | Idempotency is keyed by `profileId` and enforced by `UNIQUE(websites.profile_id)`. |
| 10 | 6.4 website.failed (new) | Reconciled | Added the `website.failed` event. |
| 11 | 7 End-to-End Event Flow | Reconciled | Added the failure path to the flow. |
| 12 | 8.3 Message Acknowledgement | Reconciled | Replaced 'will be defined during reliability design' with the outbox decision and producer rules. |
| 13 | 8.5 Validation | Reconciled | Defined poison messages. |
| 14 | 9 Event Ownership | Reconciled | Added owners for the two failure events. |

### HTTP API Contracts (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | Header | Reconciled | Added a note that this is a reconciled copy. |
| 2 | 3 Public API table | Reconciled | Added the retry endpoint to the table. |
| 3 | 3 Public API | Reconciled | Four endpoints became five. |
| 4 | 3.2 Job status response | Reconciled | Added `warnings` to the example response. |
| 5 | 3.2 Job statuses | Reconciled | Added the `PUBLISHING` job status. |
| 6 | 3.2 Warnings, error and task statuses | Reconciled | Documented `warnings`, the `error` object and the `FAILED` task status. |
| 7 | 3.3 Preview response | Reconciled | The preview response is `WebsitePreview`, which does not require ids stored inside the draft. |
| 8 | 3.4 Publish failure | Reconciled | Documented the non-conflict publish failure. |
| 9 | 3.5 Retry endpoint (new) | Reconciled | Added `POST /api/jobs/{jobId}/retry`. |
| 10 | 4 Internal API table | Reconciled | Added the internal retry-generation endpoint to the table. |
| 11 | 4.1 Preview | Reconciled | Internal preview also returns `WebsitePreview`. |
| 12 | 4.3 retry-generation (new) | Reconciled | Added the internal retry-generation endpoint. |
| 13 | 6 Error codes | Reconciled | Listed the error codes used by the API. |

### Communication Standards (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | Header | Reconciled | Added a note that this is a reconciled copy. |
| 2 | 3.2 Event names | Reconciled | Added the two failure events to the list of event names. |
| 3 | 5.3 Idempotency keys | Reconciled | Website generation is keyed by `profileId` with `UNIQUE(websites.profile_id)`. |
| 4 | 5.3 Idempotency keys | Reconciled | Added the failure event keys. |
| 5 | 8.1 Retry principles | Reconciled | Retry counts are no longer 'not finalized'. |
| 6 | 8.4 Retry strategy | Reconciled | Added the in-process retry defaults and per-stage limits (GUESS values from the source design). |
| 7 | 8.7 Dead-Letter Queues | Reconciled | Replaced the 'requires separate decisions' text with the approved DLQ design. |
| 8 | 9.3 Reliable event publication | Reconciled | The transactional outbox is decided. |
| 9 | 9.5 State transitions | Reconciled | Added the compare-and-set rule. |
| 10 | 16.2-16.3 Open decisions | Reconciled | Closed the decided SQS and reliability items. |

### CV Extraction Service (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | 7a Failure Handling (new) | Reconciled | Added failure events, retries, DLQ and the required-source rule for the CV service. |

### LinkedIn Extraction Service (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | 7a Failure Handling (new) | Reconciled | Added failure events, retries, DLQ and the optional-source rule for the LinkedIn service. |

### GitHub Analysis Service (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | 7a Failure Handling (new) | Reconciled | Added failure events, retries (including the GitHub rate-limit wait), DLQ and the optional-source rule for the GitHub service. |

### Website Service (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | 5.1 websites table | Reconciled | Added the failure-handling columns. |
| 2 | 6.2 Published events | Reconciled | Added `website.failed` to the published events. |
| 3 | 7a Failure Handling (new) | Reconciled | Added statuses, `website.failed`, the duplicate-safe claim with lease, retry-by-reuse, retries and DLQ. |

### Core Backend Service (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | 2.3 Responsibilities | Reconciled | Added consuming failure events, the watchdog and the DLQ listener. |
| 2 | 2.3 Processing rules | Reconciled | Aggregation start rule changed from 'all completed' to 'all terminal and CV completed'. |
| 3 | 2.4 Responsibilities | Reconciled | `profile.ready` is published through the outbox. |
| 4 | 5.1 jobs table | Reconciled | Pointed to the new failure-handling columns. |
| 5 | 5.1 job_tasks table | Reconciled | Pointed to the new failure-handling columns. |
| 6 | 5.1 profiles table | Reconciled | `profile_data` no longer repeats the ids. |
| 7 | 5.1 new tables and columns | GUESS | Added the failure-handling columns and the `outbox` and `dlq_seen` tables (column names are a GUESS). |
| 8 | 6.2 Event payload summary | Reconciled | Added `processing.failed` and `website.failed`. |
| 9 | 6.3 HTTP endpoints | Reconciled | Added the retry endpoint. |
| 10 | 6.3 GET job status | Reconciled | Documented `warnings` and the `error` object. |
| 11 | 7a Failure Handling (new) | Reconciled | Added the failure-handling section: aggregation rule, transitions, outbox, watchdog, DLQ listener, stale events and retry. |

### Database Architecture (reconciled).md

| # | Section | Type | Change |
| --- | --- | --- | --- |
| 1 | 5.4 Jobs status | Reconciled | Replaced the working set of statuses with the final lists from the approved failure design. |
| 2 | 5.8 websites / 5.9 new | Reconciled | Added section 5.9 with the failure-handling columns, `UNIQUE(websites.profile_id)`, and the `outbox` and `dlq_seen` tables. |
| 3 | 7.3 Unique constraints | Reconciled | Added `UNIQUE(websites.profile_id)`. |
| 4 | 5.7 / 5.8 id note | Reconciled | Table columns are the single source for ids. |
| 5 | 3.1 Mermaid diagram | Reconciled | Replaced the Mermaid diagram with one that includes the failure-handling columns, `UNIQUE(websites.profile_id)` (so `profiles` to `websites` is 1:0..1), `outbox` and `dlq_seen`. |
| 6 | 6 Cardinality | Reconciled | A profile now has at most one website (`UNIQUE(websites.profile_id)`). |
| 7 | 6.4 Website relationships | Reconciled | A profile no longer maps to multiple websites in the MVP. |
| 8 | 13.4 Open decisions | Reconciled | Struck the open question about multiple websites per profile; decided one website per profile. |
