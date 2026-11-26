# Failure Handling Design

**Project:** AI-Powered Personal Website Generator
**Scope:** MVP reliability design — fills the gaps left open in Communication Standards §8.7, §16.2 and §16.3

---

## 1. Goals and non-goals

**Goals**

1. A job never stays in a non-terminal state forever. It ends as `PREVIEW_READY`, `PUBLISHED` or `FAILED`.
   A job can finish with **warnings** when an optional source (GitHub, LinkedIn) failed but the CV worked (§6.5).
2. A user can always see that something failed and roughly why.
3. A message that keeps failing is isolated and kept for inspection, and does not block the queue.
4. A repeated `profile.ready` can never create a second website.

**Non-goals (for now)**

- Automatic redrive from DLQs. Redrive is a manual, operator-triggered step in the MVP.
- Cross-region failover.
- Refunds or billing on failure.

---

## 2. Failure model

Failures fall into three groups. They are handled differently.

| Group | Examples | Handling |
| --- | --- | --- |
| **Transient** | S3 timeout, DB connection drop, LLM 429/5xx, GitHub rate limit, worker crash | Retry. First in-process, then by SQS redelivery. |
| **Permanent (business)** | Unreadable or encrypted PDF, GitHub user not found, LLM output fails schema validation after retries, slug already taken | Do not retry. Publish a failure event, then delete the message. |
| **Poison (technical)** | Malformed JSON, unsupported `schemaVersion`, missing required field, unknown `jobId` | Do not process. Send to the DLQ. No failure event, because the identifiers cannot be trusted. |

> An LLM response that fails JSON Schema validation counts as transient for the first 2 attempts and permanent after that (see §5). LLM output is non-deterministic, so one retry often helps.

---

## 3. Failure events

The contracts currently say "No additional failure event types are introduced" (Communication Standards §8.7). This design adds two. They stay flat in the message JSON, like every other event, and reuse the common fields from SQS Event Contracts §3.1.

| Event | Queue | Producer | Consumer |
| --- | --- | --- | --- |
| `processing.failed` | `processing-results` | CV / GitHub / LinkedIn services | Core Backend (Job Orchestrator) |
| `website.failed` | `processing-results` | Website Service | Core Backend (Job Orchestrator) |

> Two events rather than one generic `*.failed`, so each has the same correlation fields as its success counterpart (`taskId` and `sourceType` for processing, `websiteId` and `profileId` for website). A single generic event would need many optional fields.

### 3.1 Failure fields (common to both events)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schemaVersion` | Integer | Yes | `1` |
| `eventId` | UUID | Yes | Unique per emission |
| `event` | String | Yes | `processing.failed` or `website.failed` |
| `occurredAt` | UTC datetime | Yes | When the failure was declared |
| `jobId` | String | Yes | Parent job |
| `userId` | String | Yes | Owner |
| `stage` | Enum | Yes | `CV_EXTRACTION`, `GITHUB_ANALYSIS`, `LINKEDIN_EXTRACTION`, `WEBSITE_GENERATION`, `WEBSITE_PUBLISHING` |
| `errorCode` | Enum | Yes | See §3.4 |
| `errorMessage` | String | Yes | Short, safe to show to a user. No stack traces, no CV text, no secrets. |
| `retryable` | Boolean | Yes | Whether the user can reasonably retry as is |
| `attempts` | Integer | Yes | How many processing attempts were made before giving up |
| `diagnosticsS3Key` | String | No | Optional pointer to a log or debug object in a private bucket |

### 3.2 `processing.failed`

Adds: `taskId` (required), `sourceType` (`CV` / `GITHUB` / `LINKEDIN`, required).

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440010",
  "event": "processing.failed",
  "occurredAt": "2026-11-17T14:31:00Z",
  "jobId": "job-456",
  "taskId": "task-789",
  "userId": "user-123",
  "sourceType": "CV",
  "stage": "CV_EXTRACTION",
  "errorCode": "SOURCE_UNREADABLE",
  "errorMessage": "The uploaded CV could not be read. It may be password protected or scanned without text.",
  "retryable": false,
  "attempts": 1
}
```

### 3.3 `website.failed`

Adds: `profileId` (required), `websiteId` (optional, because the row may not exist yet if the failure happened before the insert).

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440011",
  "event": "website.failed",
  "occurredAt": "2026-11-17T14:33:00Z",
  "jobId": "job-456",
  "userId": "user-123",
  "profileId": "profile-456",
  "websiteId": "website-456",
  "stage": "WEBSITE_GENERATION",
  "errorCode": "AI_OUTPUT_INVALID",
  "errorMessage": "We could not generate a valid website draft.",
  "retryable": true,
  "attempts": 3
}
```

### 3.4 Error codes

> The list below is a starting set. Services may add codes but must not repurpose existing ones.

| Code | Group | Typical retryable |
| --- | --- | --- |
| `SOURCE_UNREADABLE` | Permanent | No |
| `SOURCE_NOT_FOUND` (e.g. GitHub user) | Permanent | No |
| `SOURCE_EMPTY` (no usable content) | Permanent | No |
| `AI_OUTPUT_INVALID` | Permanent after retries | Yes |
| `AI_PROVIDER_UNAVAILABLE` | Transient exhausted | Yes |
| `EXTERNAL_RATE_LIMITED` | Transient exhausted | Yes |
| `STORAGE_ERROR` | Transient exhausted | Yes |
| `INTERNAL_ERROR` | Either | Yes |
| `TIMEOUT` | Raised by the Core watchdog (§6.4) | Yes |
| `RETRIES_EXHAUSTED` | Raised from a DLQ (§4.3) | Yes |
| `SLUG_TAKEN`, `PUBLISH_ASSET_ERROR` | Publishing | `SLUG_TAKEN` is a user fix |

### 3.5 Producer rules

1. Write any partial result to S3 only if it is complete and valid. Never publish a failure event that points at a half-written result.
2. Publish the failure event first, then delete the request message. If the publish fails, do not delete the message. The message is redelivered and the failure is attempted again.
3. A failure event is idempotent by `taskId` (processing) or `profileId` (website). Core ignores a failure for a task that is already `COMPLETED`, and a completion for a task that is already `FAILED` within the same attempt (see §7.3).
4. Never include user personal data in `errorMessage` or logs.

---

## 4. Retries and dead-letter queues

### 4.1 Two retry layers

| Layer | What it covers | Policy |
| --- | --- | --- |
| **In-process** | A single call to S3, GitHub, the LLM provider, etc. | Bounded exponential backoff with jitter. |
| **SQS redelivery** | The whole message, after a crash or an unacknowledged failure | Counted by SQS `ApproximateReceiveCount`, limited by `maxReceiveCount`. |

> 3 attempts per external call, base delay 1 s, factor 2, jitter ±25%, cap 15 s. Respect `Retry-After` from GitHub and the LLM provider when present.

### 4.2 Queue settings

One DLQ per source queue. This keeps each service's failures separate and lets alarms and redrive be handled per service.

| Source queue | DLQ | Visibility timeout | `maxReceiveCount` | DLQ retention |
| --- | --- | --- | --- | --- |
| `cv-extraction` | `cv-extraction-dlq` | 5 min | 3 | 14 days |
| `github-analysis` | `github-analysis-dlq` | 10 min | 3 | 14 days |
| `linkedin-extraction` | `linkedin-extraction-dlq` | 5 min | 3 | 14 days |
| `website-generation` | `website-generation-dlq` | 10 min | 3 | 14 days |
| `website-publishing` | `website-publishing-dlq` | 10 min | 3 | 14 days |
| `processing-results` | `processing-results-dlq` | 1 min | 5 | 14 days |

> Every number in this table. Reasoning:
> - Visibility timeouts are set above the expected p95 runtime of one attempt. Workers extend visibility (heartbeat) while still making progress, as Communication Standards §8 already suggests.
> - `maxReceiveCount` is 3 for LLM-backed queues because each attempt costs money and time. It is 5 for `processing-results` because handling a result is a cheap database operation, and Core is the single point that can unblock jobs.
> - Source queue retention stays at the SQS default (4 days). DLQ retention must be longer than the source queue retention.

Each DLQ must have:

- A CloudWatch alarm on `ApproximateNumberOfMessagesVisible > 0`.
- A redrive policy back to its source queue, used manually by an operator after a fix.
- The same encryption settings as its source queue.

Local environment: ElasticMQ supports `maxReceiveCount` and DLQs. Docker Compose should create the same six DLQs so the behavior can be tested locally.

### 4.3 What happens when a message reaches a DLQ

SQS moves the message silently. Nobody has told the user or Core Backend that the job failed. So each DLQ needs a consumer.

> The Core Backend runs one small **DLQ listener** that reads all six DLQs. For each message it:
> 1. Tries to parse `jobId` and, where present, `taskId` or `profileId`. A poison message with no usable ids is only logged and alarmed.
> 2. Calls the same internal "mark failed" operation that `processing.failed` / `website.failed` use, with `errorCode = RETRIES_EXHAUSTED` and `retryable = true`.
> 3. Leaves the message in the DLQ. It is not deleted, so an operator can inspect and redrive it.
>
> To avoid reprocessing the same DLQ message, the listener records the DLQ `messageId` in a `dlq_seen` table (or uses the same idempotent "mark failed" check). It does not rely on deleting messages.

An alternative is an AWS Lambda per DLQ. The listener-in-Core approach is assumed here because it keeps all job state transitions in one service, and Core is the owner of job and task status.

### 4.4 Which failures skip the DLQ

- **Permanent business failures** publish the failure event and delete the request message right away. There is no point in burning three more attempts.
- **Poison messages** are not deleted. They are allowed to reach `maxReceiveCount` and then land in the DLQ. They could also be sent to the DLQ immediately by the consumer.

---

## 5. Retry limits per stage (summary)

> all values.

| Stage | External call retries (in-process) | LLM-output validation retries | SQS receives | Worst case before `FAILED` |
| --- | --- | --- | --- | --- |
| CV extraction | 3 | 2 | 3 | ~3 × 5 min |
| GitHub analysis | 3, plus rate-limit wait up to 60 s | 2 | 3 | ~3 × 10 min |
| LinkedIn extraction | 3 | 2 | 3 | ~3 × 5 min |
| Website generation | 3 | 2 | 3 | ~3 × 10 min |
| Core handling `processing-results` | 3 (DB) | n/a | 5 | ~5 × 1 min |
| Website publishing (async via `website.publish.requested`) | Render-worker call: 3 retries with backoff on 5xx or timeout. No automatic redelivery loop beyond the queue's 3 receives. Safe for the user to repeat. | 10 s per render call | 5 min visibility | `website-publishing` DLQ after 3 receives |

Publishing is asynchronous (HTTP `202`, then the `website.publish.requested` event; HTTP API Contracts §3.4 and §4.2) and is already idempotent for the same `websiteId + slug` (Communication Standards §5.4). The frontend may repeat it.

---

## 6. Status lists

The existing documents leave statuses open (Database Architecture §5.4, §7.4). The job list in HTTP API Contracts §3.2 is the only concrete one. This section builds on it.

### 6.1 Job status (`jobs.status`)

Owner: Core Backend.

| Status | Meaning | Terminal |
| --- | --- | --- |
| `QUEUED` | Job created, tasks not yet dispatched | No |
| `PROCESSING` | At least one source task is pending | No |
| `AGGREGATING` | All requested tasks completed, profile being built | No |
| `GENERATING` | `profile.ready` published, website draft being generated | No |
| `PREVIEW_READY` | Draft available for preview | No (user decides) |
| `PUBLISHING` | **New.** User requested publication, in progress | No |
| `PUBLISHED` | Website live | Yes |
| `FAILED` | Job cannot continue | Yes |

> Add `PUBLISHING`. The HTTP contract lists `PUBLISHED` but has no state for the time when publishing is running, and recovery from a half-finished publish (Communication Standards §9.4) needs one.

Additional columns on `jobs`:

| Column | Purpose |
| --- | --- |
| `failed_stage` | The `stage` value of the failure |
| `error_code` | Last failure code |
| `error_message` | User-safe message |
| `failed_at` | When the job entered `FAILED` |
| `status_changed_at` | Used by the watchdog (§6.4) |

### 6.2 Task status (`job_tasks.status`)

Owner: Core Backend.

| Status | Meaning | Terminal |
| --- | --- | --- |
| `PENDING` | Request event published, waiting for a result | No |
| `COMPLETED` | Result recorded | Yes |
| `FAILED` | Terminal failure reported or inferred | Yes |

**Optional-source failure (confirmed).** A `FAILED` GitHub or LinkedIn task does **not** fail the job. Aggregation starts when every requested task is terminal (`COMPLETED` or `FAILED`) **and the CV task is `COMPLETED`**. Failed optional sources are left out of the profile and recorded as warnings (§6.5). A `FAILED` CV task fails the job.

The CV is the required source (confirmed).

> No `PROCESSING` task status. The AI services never write to Core's database and there is no "started" event, so Core cannot know when work actually begins. Adding a `*.started` event is possible but is more traffic for little gain. The job-level `PROCESSING` covers the user-facing need.

Additional columns: `attempt` (integer, default 1), `error_code`, `error_message`, `failed_at`.

### 6.3 Website status (`websites.status`)

Owner: Website Service. Synchronised to the job by events (`website.generated`, `website.failed`, `website.published`).

| Status | Meaning | Terminal |
| --- | --- | --- |
| `GENERATING` | Row created, draft being produced | No |
| `GENERATION_FAILED` | Draft could not be produced | Yes (until a new job) |
| `PREVIEW_READY` | Draft stored and valid | No |
| `PUBLISHING` | Slug reserved, assets being uploaded | No |
| `PUBLISH_FAILED` | Publishing failed after slug reservation | No (can be retried) |
| `PUBLISHED` | Static files uploaded, URL live | Yes |

Additional columns: `generation_lease_expires_at`, `error_code`, `error_message`.

### 6.5 Warnings for skipped optional sources

> `jobs.warnings` (JSONB array, default `[]`). Each entry is `{ "sourceType": "GITHUB", "errorCode": "SOURCE_NOT_FOUND", "message": "..." }`.

- Core appends a warning when a GITHUB or LINKEDIN task becomes `FAILED` while the job is still alive.
- `GET /api/jobs/{jobId}` returns `warnings` at any status, so the frontend can show "GitHub could not be imported, your site was built from your CV" next to the preview.
- Warnings do not change `status`. A job in `PREVIEW_READY` with warnings is a success.
- The user may retry a skipped source (§8).

### 6.4 Allowed transitions

A transition is applied only with a compare-and-set, for example `UPDATE jobs SET status = :new WHERE id = :id AND status = ANY(:allowed_from)`. If zero rows change, the event is a duplicate or stale one and is acknowledged without side effects. This implements the rule in SQS Event Contracts §8.2 ("reject transitions that would overwrite newer durable states").

**Job**

```
QUEUED ──► PROCESSING ──► AGGREGATING ──► GENERATING ──► PREVIEW_READY ──► PUBLISHING ──► PUBLISHED
   │            │               │              │               │                │
   └────────────┴───────────────┴──────────────┴───────────────┴────────────────┴──► FAILED
                                                                            PUBLISHING ──► PREVIEW_READY  (publish failed, user may retry)
```

Notes:

- `FAILED` is reachable from any non-terminal state. From `PROCESSING` it happens only for a CV failure, a timeout, or when no required task can complete. An optional-source failure does not move the job to `FAILED` (§6.2).
- A failure during publishing returns the job to `PREVIEW_READY` and the website to `PUBLISH_FAILED`. The draft is still fine, so the user does not lose it. The job is **not** `FAILED` in this case. (Confirmed.)
- `PUBLISHED` and `FAILED` accept no further transitions, except the user-initiated retry in §8.

**Watchdog.** A scheduled job in Core checks `status_changed_at` and fails jobs that stay in a non-terminal state too long.

> Thresholds: `QUEUED` 5 min, `PROCESSING` 30 min, `AGGREGATING` 5 min, `GENERATING` 30 min, `PUBLISHING` 10 min. A timed-out job is failed with `errorCode = TIMEOUT`. This covers the case where an event is lost completely, which the DLQ cannot see.

---

## 7. Duplicate `profile.ready` must not create a second website

### 7.1 The rule

**One website per unified profile. One profile per job.** The database enforces both, so correctness never depends on in-memory checks or on `eventId`.

| Layer | Constraint | Source |
| --- | --- | --- |
| Profile per job | `UNIQUE(profiles.job_id)` | Already proposed, Database Architecture §7.3 |
| Website per profile | `UNIQUE(websites.profile_id)` | **New** |

> `profile_id` is the natural idempotency key for generation, because `profile.ready` carries it and the existing key table says "jobId / profileId" for website generation (Communication Standards §5.3). Because profile is 1:1 with job, the two are equivalent. The constraint is placed on `profile_id` so it also holds if the job↔profile link changes later.

### 7.2 Website Service handling of `profile.ready`

```
on message profile.ready (jobId, userId, profileId, templateId):
  1. Validate against schema. Poison → leave unacked (goes to DLQ).
  2. Verify the profile exists and belongs to userId and jobId (read-only).
  3. Atomically claim the generation:
       INSERT INTO websites (id, user_id, profile_id, template_id, status,
                             generation_lease_expires_at)
       VALUES (:new_id, :userId, :profileId, :templateId, 'GENERATING', now() + interval '15 min')
       ON CONFLICT (profile_id) DO NOTHING
       RETURNING id;
  4. If a row was returned → this worker owns the generation. Go to step 6.
  5. Otherwise read the existing row and decide:
       status = PREVIEW_READY | PUBLISHING | PUBLISH_FAILED | PUBLISHED
            → work is already done. Re-publish website.generated (harmless, idempotent in Core).
              Delete the message.
       status = GENERATION_FAILED
            → failure was already reported. Delete the message.
       status = GENERATING and lease not expired
            → another worker is on it. Do NOT delete the message.
              Set visibility to the lease remainder so it is retried later.
       status = GENERATING and lease expired
            → previous worker died. Take over atomically:
              UPDATE websites SET generation_lease_expires_at = now() + interval '15 min'
              WHERE id = :id AND status = 'GENERATING' AND generation_lease_expires_at < now()
              (1 row updated → this worker now owns it. 0 rows → someone else did, re-evaluate.)
  6. Generate and validate the draft. Extend visibility and renew the lease while working.
  7. UPDATE websites SET draft_content = ..., status = 'PREVIEW_READY'
        WHERE id = :id AND status = 'GENERATING'.
  8. Publish website.generated. Delete the message.
```

Why this is safe:

- Two workers racing on the same message: only one `INSERT ... ON CONFLICT DO NOTHING` returns a row. The other falls into step 5.
- A duplicate that arrives **after** completion does not regenerate anything and does not call the LLM again.
- A duplicate that arrives **during** generation is not acknowledged, so if the owner crashes the message is still available for recovery. This is why step 5 must not simply delete it.
- If the worker crashes after step 7 but before step 8, the next delivery finds `PREVIEW_READY` and re-publishes `website.generated`. Core must treat that event idempotently (it already must, by §8.1 of the SQS contracts).

### 7.3 Core Backend: same treatment upstream

Duplicates of `profile.ready` are only possible if Core publishes it more than once. Core should also be safe:

- Aggregation is guarded by the transition `PROCESSING → AGGREGATING` (compare-and-set). Only the caller that changes one row proceeds. A second `processing.completed` that arrives afterwards changes zero rows and is ignored.
- Profile insert uses `UNIQUE(profiles.job_id)` with `ON CONFLICT DO NOTHING`.
- `profile.ready` is published through a **transactional outbox**: the profile row, the `AGGREGATING → GENERATING` transition and an `outbox` row are written in one transaction. A relay publishes from the outbox and marks rows sent. If the relay crashes between publish and mark, the event is published twice. That is acceptable, because §7.2 handles it.

> Use the outbox for the events Core publishes (`cv.extract.requested`, `github.analyze.requested`, `linkedin.extract.requested`, `profile.ready`). The services that publish `processing.completed`, `processing.failed`, `website.generated`, etc. do not have a DB of their own in the CV/GitHub/LinkedIn case, so they rely on "publish, then delete the request message, otherwise redeliver" (§3.5).

### 7.4 Stale and out-of-order events in Core

| Situation | Behavior |
| --- | --- |
| `processing.completed` for a task already `FAILED` | Ignored and logged. (Only possible without a retry, or with a stale `attempt`.) |
| `processing.failed` for an optional source after aggregation has started | Task is marked `FAILED` and a warning is added, but aggregation is not redone. |
| `processing.failed` for a task already `COMPLETED` | Ignored and logged. |
| Any event for a job already `FAILED` | Ignored, except `website.published` for a website that really was published (it is recorded, and the job is moved to `PUBLISHED` only if allowed by §6.4). |
| Event for an unknown `jobId` or `taskId` | Logged, then the message goes to the DLQ (Core §8.5 says completion events must match existing jobs). |
| Event carrying an older `attempt` than the task's current one (after a retry, §8) | Ignored. |

---

## 8. User-visible failure and retry

> The MVP offers a single user-initiated retry, via a new endpoint `POST /api/jobs/{jobId}/retry`. It is only valid when `status = FAILED` and the failed `retryable = true`.

- Retrying a skipped optional source (job in `PREVIEW_READY` with a warning) is a separate case. It would change the profile after the website was generated, so for the MVP it creates a new job rather than reusing the old one.
- Retrying a source failure (CV failure, job `FAILED`) resets only the failed tasks to `PENDING`, increments `job_tasks.attempt`, and re-publishes the request events. The existing task row is reused, which fits the proposed `UNIQUE(job_id, source_type)` constraint ("repeated attempts reuse the same logical task").
- Request events gain an optional `attempt` field, and completion/failure events echo it. This lets Core drop stale results from the previous attempt (§7.4).
- Retrying a website-generation failure (confirmed) **reuses the same website row**: the job goes `FAILED → GENERATING`, the website goes `GENERATION_FAILED → GENERATING` with a fresh lease, and Core re-publishes `profile.ready` for the same `profileId`. `UNIQUE(websites.profile_id)` therefore still holds and no duplicate is created. The Website Service's step 5 must treat a `GENERATION_FAILED` row that comes with a retry as claimable (see below).

> To tell a retry from a stale duplicate, the retry sets `websites.status = 'GENERATING'` itself through the Website Service's internal API before re-publishing, so the normal "claim" path in §7.2 sees `GENERATING` with an expired or fresh lease. A stale duplicate arriving later for a `GENERATION_FAILED` row is still just deleted.
- `GET /api/jobs/{jobId}` response gains `error: { code, message, stage, retryable }` when `FAILED`, using the same shape as the standard HTTP error object.

---

## 9. Observability

- Log every failure with `jobId`, `taskId`, `eventId`, `stage`, `errorCode`, `attempt` and `receiveCount`. No personal data.
- Metrics per queue: DLQ depth, age of oldest message, receive-count histogram, failure events per `errorCode`.
- Alarms: any message in any DLQ; job watchdog timeouts above a threshold; `processing-results` queue age.
- Add `failed-jobs` to the operational dashboard (count by `failed_stage` and `errorCode`).

---

## 10. Decisions

1. **Optional sources.** A GitHub or LinkedIn failure does not fail the job. The job continues with the CV and the user gets a warning (§6.2, §6.5).
2. **Publish failure.** A failed publish returns the job to `PREVIEW_READY` and keeps the draft (§6.4).
3. **Retry of a failed generation.** It reuses the same website row, so no duplicate is created (§8).
4. **Numbers.** The retry counts, visibility timeouts and watchdog limits in §4–§6 are starting values, tuned after measuring real runtimes.
5. **Failure event style.** Two events: `processing.failed` and `website.failed`.
6. **DLQ listener** runs in the Core Backend.
7. **Outbox.** A transactional outbox in Core (and in the Website Service) for the events they publish.
8. **CV required.** The CV is mandatory, so the aggregation rule in §6.2 stands.

