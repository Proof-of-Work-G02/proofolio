# SQS Event Contracts

**Project:** AI-Powered Personal Website Generator  
**Scope:** MVP / Happy Flow  
**Communication Technology:** Amazon SQS Standard (AWS) / ElasticMQ (Local)

## 1. Purpose

This document defines the asynchronous communication contracts between the application's microservices.

It specifies the SQS queues, event types, message payloads, producers, consumers, validation requirements, and message processing rules.

The objective is to establish consistent event interfaces that enable independently developed services to communicate reliably without requiring direct synchronous dependencies.

The contracts cover communication between:

- Core Backend Service
- CV Extraction Service
- GitHub Analysis Service
- LinkedIn Extraction Service
- Website Service

Large documents and processing results are exchanged through private Amazon S3 storage rather than embedded directly in SQS messages.

## 2. Messaging Architecture

The application uses Amazon SQS Standard for asynchronous communication between services.

Each AI Processing Service has a dedicated request queue. Website generation and website publishing each have their own queue.

A shared results queue is used to deliver processing completion and website lifecycle events to the Core Backend Service.

### 2.1 Queue Configuration

The MVP defines six SQS queues.

| Queue | Producer | Consumer | Purpose |
| --- | --- | --- | --- |
| `cv-extraction` | Core Backend | CV Extraction Service | Distribute CV extraction tasks |
| `github-analysis` | Core Backend | GitHub Analysis Service | Distribute GitHub analysis tasks |
| `linkedin-extraction` | Core Backend | LinkedIn Extraction Service | Distribute LinkedIn extraction tasks |
| `website-generation` | Core Backend | Website Service | Trigger website generation |
| `website-publishing` | Website Service (outbox) | Website Service (Website Publisher) | Trigger asynchronous website publishing |
| `processing-results` | AI Services / Website Service | Core Backend | Deliver processing and website completion events |

**Messaging Principles**

- Each queue has one logical consuming service.
- Multiple worker instances of the same service may consume messages from its queue.
- SQS Standard provides at-least-once delivery.
- Strict message ordering is not guaranteed.
- Consumers must support idempotent processing.
- Messages must contain identifiers and references rather than large documents.
- Queue URLs are configured separately for each environment.

### 2.1.1 Dead-Letter Queues

Each source queue has one dead-letter queue (DLQ), so each service's failures stay separate.

| Source queue | DLQ | Visibility timeout | `maxReceiveCount` | DLQ retention |
| --- | --- | --- | --- | --- |
| `cv-extraction` | `cv-extraction-dlq` | 5 min | 3 | 14 days |
| `github-analysis` | `github-analysis-dlq` | 10 min | 3 | 14 days |
| `linkedin-extraction` | `linkedin-extraction-dlq` | 5 min | 3 | 14 days |
| `website-generation` | `website-generation-dlq` | 10 min | 3 | 14 days |
| `website-publishing` | `website-publishing-dlq` | 10 min | 3 | 14 days |
| `processing-results` | `processing-results-dlq` | 1 min | 5 | 14 days |

- Workers extend visibility (heartbeat) while they are still making progress.
- DLQ retention must be longer than the source queue retention (SQS default, 4 days).
- Each DLQ has a CloudWatch alarm on `ApproximateNumberOfMessagesVisible > 0`, the same encryption as its source queue, and a redrive policy back to the source queue. Redrive is a manual operator step in the MVP.
- Local development creates the same six DLQs in ElasticMQ.
- A DLQ listener in the Core Backend reads all six DLQs. It marks the affected job, task or website as failed with `errorCode = RETRIES_EXHAUSTED`, records the DLQ `messageId` in a `dlq_seen` table, and leaves the message in the DLQ. A poison message with no usable ids is only logged and alarmed.

### 2.2 Event Registry

The MVP defines ten event types.

| Event | Queue | Producer | Consumer |
| --- | --- | --- | --- |
| `cv.extract.requested` | cv-extraction | Job Orchestrator | CV Extractor |
| `github.analyze.requested` | github-analysis | Job Orchestrator | GitHub Analyzer |
| `linkedin.extract.requested` | linkedin-extraction | Job Orchestrator | LinkedIn Extractor |
| `processing.completed` | processing-results | AI Processing Services | Job Orchestrator |
| `profile.ready` | website-generation | Profile Aggregator | Website Generator |
| `website.generated` | processing-results | Website Generator | Job Orchestrator |
| `website.publish.requested` | website-publishing | Website Service (outbox) | Website Publisher |
| `website.published` | processing-results | Website Publisher | Core Backend |
| `processing.failed` | processing-results | AI Processing Services | Job Orchestrator |
| `website.failed` | processing-results | Website Generator / Publisher | Job Orchestrator |

No additional event is required between the Job Orchestration Module and Profile Aggregation Module, because both belong to the same Core Backend Service.

## 3. Common Event Structure

All SQS messages use JSON encoded as UTF-8.

### 3.1 Common Message Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| schemaVersion | Integer | Yes | Version of the event contract |
| eventId | String (UUID) | Yes | Unique identifier for the emitted event |
| event | String | Yes | Event type |
| occurredAt | String (UTC datetime) | Yes | Timestamp when the event was emitted |
| jobId | String | Yes | Associated processing job identifier |
| taskId | String | Event-specific | Associated extraction or analysis task |
| userId | String | Event-specific | Associated application user identifier |
| attempt | Integer | No | Retry attempt number (default 1). Request events may carry it; completion and failure events echo it so Core can drop results from an older attempt |

**Convention**

All MVP events use `schemaVersion: 1`.

The event metadata is included directly in the message JSON rather than inside a separate envelope object.

Example:

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440000",
  "event": "cv.extract.requested",
  "occurredAt": "2026-11-17T14:30:00Z",
  "jobId": "job-456",
  "taskId": "task-789",
  "userId": "user-123",
  "cvS3Key": "user-123/job-456/cv.pdf"
}
```

The precise required business fields depend on the event type.

The final schemas are defined and validated using the shared JSON Schema specifications.

### 3.2 Message Correlation

Each processing job receives a unique `jobId`.

Each source-specific processing task receives a unique `taskId`.

These identifiers are used to correlate processing requests and completion events.

**Correlation Rules**

- `jobId` identifies the overall portfolio generation workflow.
- `taskId` identifies an individual AI processing task.
- `eventId` identifies a particular event emission.
- `userId` identifies the associated application user where needed.
- `websiteId` identifies the generated website after website creation.

A processing job may contain multiple tasks, but every task belongs to exactly one processing job.

The Core Backend Service maintains the authoritative mapping between jobs, tasks, and users in PostgreSQL.

## 4. Processing Request Events

The following events are published by the Core Backend Service to initiate source-specific processing.

### 4.1 Event — cv.extract.requested

**Producer:** Core Backend / Job Orchestration Module  
**Consumer:** CV Extraction Service  
**Queue:** `cv-extraction`

**Purpose**

Requests extraction of structured professional information from a user-uploaded CV document.

**Trigger**

The Core Backend Service successfully validates the uploaded CV, stores it in private Amazon S3 storage, and creates the corresponding processing task.

**Payload**

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440001",
  "event": "cv.extract.requested",
  "occurredAt": "2026-11-17T14:30:00Z",
  "jobId": "job-456",
  "taskId": "task-789",
  "userId": "user-123",
  "cvS3Key": "user-123/job-456/cv.pdf"
}
```

**Business Fields**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| jobId | String | Yes | Parent processing job |
| taskId | String | Yes | CV extraction task |
| userId | String | Yes | Associated application user |
| cvS3Key | String | Yes | CV object key in private uploads bucket |

**Consumer Responsibilities**

1. Receive and validate the message.
2. Retrieve the CV document from private S3 storage.
3. Extract its textual content.
4. Convert the extracted information into structured JSON.
5. Validate the output against the shared CV extraction schema.
6. Store the structured result in private S3 storage.
7. Publish a `processing.completed` event.

**Expected Output**

A JSON extraction result stored in the configured `extraction-results` bucket.

Example object key:

`job-456/task-789/cv.json`

The CV Extraction Service does not modify the Core Backend PostgreSQL database.

### 4.2 Event — github.analyze.requested

**Producer:** Core Backend / Job Orchestration Module  
**Consumer:** GitHub Analysis Service  
**Queue:** `github-analysis`

**Purpose**

Requests analysis of a user's public GitHub repositories to extract technical skills, projects, and supporting evidence.

**Trigger**

The user submits a GitHub username or profile URL, and the Core Backend creates a GitHub analysis task.

**Payload**

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440002",
  "event": "github.analyze.requested",
  "occurredAt": "2026-11-17T14:30:00Z",
  "jobId": "job-456",
  "taskId": "task-790",
  "userId": "user-123",
  "githubUsername": "example-user"
}
```

**Business Fields**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| jobId | String | Yes | Parent processing job |
| taskId | String | Yes | GitHub analysis task |
| userId | String | Yes | Associated application user |
| githubUsername | String | Yes | Normalized GitHub username |

The event carries no GitHub token. The GitHub Analysis Service calls the GitHub REST API with its own server-side token and reads public data only.

**Consumer Responsibilities**

1. Validate the processing request.
2. Retrieve public repositories using the GitHub REST API.
3. Retrieve repository metadata, directory structures, and relevant file names.
4. Retrieve README documentation.
5. Analyze project descriptions, technologies, and documented functionality.
6. Produce structured JSON with supporting technical evidence.
7. Store the result in private S3 storage.
8. Publish a `processing.completed` event.

**Expected Output**

`job-456/task-790/github.json`

The MVP does not require repository cloning, code execution, or private repository access.

### 4.3 Event — linkedin.extract.requested

**Producer:** Core Backend / Job Orchestration Module  
**Consumer:** LinkedIn Extraction Service  
**Queue:** `linkedin-extraction`

**Purpose**

Requests extraction of structured professional information from a user-exported LinkedIn profile PDF.

**Trigger**

The user uploads a LinkedIn PDF, and the Core Backend validates and stores the document.

**Payload**

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440003",
  "event": "linkedin.extract.requested",
  "occurredAt": "2026-11-17T14:30:00Z",
  "jobId": "job-456",
  "taskId": "task-791",
  "userId": "user-123",
  "linkedinS3Key": "user-123/job-456/linkedin-profile.pdf"
}
```

**Business Fields**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| jobId | String | Yes | Parent processing job |
| taskId | String | Yes | LinkedIn extraction task |
| userId | String | Yes | Associated application user |
| linkedinS3Key | String | Yes | LinkedIn PDF object key in private uploads bucket |

**Consumer Responsibilities**

1. Validate the message.
2. Retrieve the LinkedIn PDF from private S3 storage.
3. Extract textual information.
4. Identify education, experience, skills, certifications, and other available professional information.
5. Normalize the extracted information into structured JSON.
6. Validate the result using the shared extraction schema.
7. Store the result in private S3 storage.
8. Publish a `processing.completed` event.

**Expected Output**

`job-456/task-791/linkedin.json`

The MVP relies on explicitly user-provided documents and does not use LinkedIn scraping or LinkedIn API authentication.

## 5. Processing Completion Event

### 5.1 Event — processing.completed

**Producer:** CV Extraction / GitHub Analysis / LinkedIn Extraction Services  
**Consumer:** Core Backend / Job Orchestration Module  
**Queue:** `processing-results`

**Purpose**

Indicates that an AI processing task has completed successfully and that its structured result is available in private S3 storage.

All three AI Processing Services publish this event using the same contract.

**Trigger**

The processing service completes extraction or analysis, validates its generated JSON, and successfully stores the result in S3.

**Payload**

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440004",
  "event": "processing.completed",
  "occurredAt": "2026-11-17T14:31:00Z",
  "jobId": "job-456",
  "taskId": "task-789",
  "sourceType": "CV",
  "status": "COMPLETED",
  "resultS3Key": "job-456/task-789/cv.json"
}
```

**Business Fields**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| jobId | String | Yes | Associated processing job |
| taskId | String | Yes | Completed task |
| sourceType | Enum | Yes | CV, GITHUB, LINKEDIN |
| status | String | Yes | COMPLETED |
| resultS3Key | String | Yes | Extraction result object key |

**Supported Source Types**

- `CV`
- `GITHUB`
- `LINKEDIN`

**Consumer Responsibilities**

1. Receive and validate the completion event.
2. Identify the corresponding job and task in PostgreSQL.
3. Verify the task's source type and job association.
4. Retrieve the structured result from private S3 storage.
5. Validate the result against the appropriate source-specific schema.
6. Record the result or its reference in PostgreSQL.
7. Mark the task as completed.
8. Check whether every requested processing task is terminal (`COMPLETED` or `FAILED`).

Aggregation starts when every requested task is terminal and the CV task is `COMPLETED`. A failed optional (GitHub or LinkedIn) task is left out of the profile and recorded as a job warning; a failed CV task fails the job (see `processing.failed`).

**Important Rules**

- Only requested processing tasks are considered.
- Missing optional sources do not block aggregation.
- Duplicate completion events must not trigger duplicate aggregation.
- The result must be stored successfully before the completion event is published.

No `aggregation.requested` SQS event is required.

### 5.2 Event — processing.failed

**Producer:** CV Extraction / GitHub Analysis / LinkedIn Extraction Services  
**Consumer:** Core Backend / Job Orchestration Module  
**Queue:** `processing-results`

**Purpose**

Indicates that an AI processing task cannot succeed and gives a reason that is safe to show to a user.

**Trigger**

The service hits a permanent business failure (for example an unreadable PDF or an unknown GitHub user), or it has exhausted its in-process retries and LLM-output validation retries. Poison messages (malformed JSON, unsupported `schemaVersion`, missing required field, unknown `jobId`) do **not** produce this event; they are left to reach the DLQ.

**Payload**

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

**Business Fields**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| jobId | String | Yes | Parent processing job |
| taskId | String | Yes | Failed task |
| userId | String | Yes | Associated application user |
| sourceType | Enum | Yes | CV, GITHUB, LINKEDIN |
| stage, errorCode, errorMessage, retryable, attempts, diagnosticsS3Key | | | `FailureInfo` (Shared Data Contracts §3.3) |
| attempt | Integer | No | Echo of the request's `attempt` |

**Producer Rules**

1. Never write a partial result to S3, and never publish a failure event that points at a half-written result.
2. Publish the failure event first, then delete the request message. If publishing fails, do not delete the message; it is redelivered and the failure is attempted again.
3. Never put personal data in `errorMessage` or logs.

**Consumer Responsibilities**

1. Validate the event and find the job and task. An unknown `jobId` or `taskId` is logged and the message goes to the DLQ.
2. Apply the transition with a compare-and-set (a repeated or stale event changes zero rows and is acknowledged).
3. Mark the task `FAILED` and store `error_code`, `error_message`, `failed_at`.
4. If the task is the **CV**, mark the job `FAILED`. If it is **GitHub or LinkedIn**, keep the job alive and append a `JobWarning` (Shared Data Contracts §3.4).
5. If every requested task is now terminal and the CV is `COMPLETED`, trigger profile aggregation.

**Important Rules**

- Idempotent by `taskId`. A failure for a task that is already `COMPLETED` is ignored and logged. A completion for a task that is already `FAILED` (same attempt) is ignored and logged.
- An event with an `attempt` older than the task's current attempt is ignored.

## 6. Website Events

### 6.1 Event — profile.ready

**Producer:** Core Backend / Profile Aggregation Module  
**Consumer:** Website Service / Website Generator Module  
**Queue:** `website-generation`

**Purpose**

Notifies the Website Service that a unified user profile is available and website generation can begin.

**Trigger**

The Profile Aggregation Module successfully combines the completed extraction results and stores the unified profile in PostgreSQL.

**Payload**

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440005",
  "event": "profile.ready",
  "occurredAt": "2026-11-17T14:32:00Z",
  "jobId": "job-456",
  "userId": "user-123",
  "profileId": "profile-456",
  "templateId": "template-001"
}
```

**Business Fields**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| jobId | String | Yes | Associated processing job |
| userId | String | Yes | Profile owner |
| profileId | String | Yes | Unified profile identifier |
| templateId | String | Yes | Selected website template |

**Consumer Responsibilities**

1. Validate the event.
2. Retrieve the unified profile from PostgreSQL.
3. Retrieve the selected website template.
4. Generate personalized website content using the AI provider.
5. Produce a website draft compatible with the selected template.
6. Validate the generated content.
7. Store the website draft and metadata in PostgreSQL.
8. Publish a `website.generated` event.

**Important Rules**

The event contains a profile identifier, not the complete unified profile.

The Website Service may read the profile data it requires but must not modify profile information owned by the Core Backend Service.

Repeated delivery of `profile.ready` must not create duplicate websites. The Website Service claims generation with `INSERT ... ON CONFLICT (profile_id) DO NOTHING` against `UNIQUE(websites.profile_id)`, so one profile yields at most one website. A claim carries a lease (`generation_lease_expires_at`) so a crashed worker's generation can be taken over.

### 6.2 Event — website.generated

**Producer:** Website Service / Website Generator Module  
**Consumer:** Core Backend / Job Orchestration Module  
**Queue:** `processing-results`

**Purpose**

Indicates that the Website Service has successfully generated and stored a website draft.

**Trigger**

The Website Generator completes generation and persists the unpublished website draft in PostgreSQL.

**Payload**

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440006",
  "event": "website.generated",
  "occurredAt": "2026-11-17T14:33:00Z",
  "jobId": "job-456",
  "userId": "user-123",
  "profileId": "profile-456",
  "websiteId": "website-456",
  "status": "PREVIEW_READY"
}
```

**Business Fields**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| jobId | String | Yes | Associated processing job |
| userId | String | Yes | Website owner |
| profileId | String | Yes | Source unified profile |
| websiteId | String | Yes | Generated website identifier |
| status | String | Yes | PREVIEW\_READY |

**Consumer Responsibilities**

1. Receive and validate the event.
2. Identify the corresponding processing job.
3. Record the generated website identifier.
4. Update the job status to `PREVIEW_READY`.
5. Make the website available for frontend preview.

The Frontend subsequently retrieves the draft using:

`GET /api/websites/{websiteId}/preview`

The website is not publicly accessible at this stage.

No subdomain is reserved during generation.

### 6.3 Event — website.publish.requested

**Producer:** Website Service (transactional outbox)  
**Consumer:** Website Service / Website Publisher Module  
**Queue:** `website-publishing`

**Purpose**

Requests that an approved website draft be rendered and published to its public subdomain.

**Trigger**

The user approves the website and calls `POST /api/websites/{websiteId}/publish`. The Website Service validates the slug and, in one transaction, moves the website to `PUBLISHING` with a compare-and-set, reserves the slug, and writes an outbox row. A relay publishes the row to the `website-publishing` queue. The HTTP call returns `202 Accepted` with status `PUBLISHING`; the frontend then polls the job status.

**Payload**

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440012",
  "event": "website.publish.requested",
  "occurredAt": "2026-11-17T14:34:00Z",
  "jobId": "job-456",
  "userId": "user-123",
  "websiteId": "website-456",
  "slug": "alex-popescu"
}
```

**Business Fields**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| jobId | String | Yes | Associated processing job |
| userId | String | Yes | Website owner |
| websiteId | String | Yes | Website to publish |
| slug | String | Yes | Reserved subdomain slug |

**Consumer Responsibilities**

1. Validate the event and load the website in `PUBLISHING` state.
2. Call the render worker (a Node Lambda container image) with HMAC service-to-service authentication to render the static site from the draft and its template.
3. Upload the static files to S3, with `index.html` last.
4. Mark the website `PUBLISHED` and store the publishing metadata.
5. Publish `website.published`. On failure, publish `website.failed` with `stage = WEBSITE_PUBLISHING`.

**Important Rules**

- Repeated delivery must not publish twice. The publisher applies its transitions with a compare-and-set on the website status.
- The queue has its own DLQ (`website-publishing-dlq`); a message that exhausts its retries marks the website `PUBLISH_FAILED` with `RETRIES_EXHAUSTED`.
- Re-uploading the same files to the same slug is safe, so a retried publish is idempotent.

### 6.4 Event — website.published

**Producer:** Website Service / Website Publisher Module  
**Consumer:** Core Backend Service  
**Queue:** `processing-results`

**Purpose**

Indicates that a website has been successfully published and is available through its assigned public subdomain.

**Trigger**

The Website Publisher consumes `website.publish.requested`, renders the site, uploads the static assets to S3, and stores the publishing metadata.

**Payload**

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440007",
  "event": "website.published",
  "occurredAt": "2026-11-17T14:35:00Z",
  "jobId": "job-456",
  "userId": "user-123",
  "websiteId": "website-456",
  "slug": "alex-popescu",
  "status": "PUBLISHED",
  "url": "https://alex-popescu.ourdomain.com"
}
```

**Business Fields**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| jobId | String | Yes | Associated processing job |
| userId | String | Yes | Website owner |
| websiteId | String | Yes | Published website identifier |
| slug | String | Yes | Unique website subdomain |
| status | String | Yes | PUBLISHED |
| url | String | Yes | Public website URL |

**Consumer Responsibilities**

1. Receive and validate the event.
2. Identify the associated job and website.
3. Move the job from `PUBLISHING` to its published state.
4. Record the published website URL.
5. Make the final URL available to the Frontend through job status polling.

**Important Rules**

- Publishing requires explicit user approval.
- Slug uniqueness is enforced by PostgreSQL. If a slug is taken by another user, the publish request is rejected with `409 SLUG_TAKEN`; if the same user republishes, the previous website with that slug becomes `UNPUBLISHED` (slug takeover).
- The event is published only after the publication operation succeeds.
- Repeated publication events must not create duplicate state changes.
- Public requests to the published website are handled by CloudFront and S3, not the Website Service.

The `202 Accepted` response to the publish request only acknowledges that publishing has started. This event is the confirmation that publishing finished, and it is how the Core Backend learns the final URL.

### 6.5 Event — website.failed

**Producer:** Website Service  
**Consumer:** Core Backend / Job Orchestration Module  
**Queue:** `processing-results`

**Purpose**

Indicates that website generation or publishing failed.

**Payload**

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

**Business Fields**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| jobId | String | Yes | Associated processing job |
| userId | String | Yes | Website owner |
| profileId | String | Yes | Source unified profile |
| websiteId | String | No | Absent when the failure happened before the `websites` row was created |
| stage, errorCode, errorMessage, retryable, attempts, diagnosticsS3Key | | | `FailureInfo` (Shared Data Contracts §3.3) |

**Consumer Responsibilities**

- `stage = WEBSITE_GENERATION`: the website is `GENERATION_FAILED`; Core moves the job to `FAILED`.
- `stage = WEBSITE_PUBLISHING`: the website is `PUBLISH_FAILED`; Core returns the job from `PUBLISHING` to `PREVIEW_READY` and does **not** mark it `FAILED`, so the user keeps the draft and may try again.
- Idempotent by `profileId`. Apply transitions with a compare-and-set.

**Producer Rules**

Same as `processing.failed`: publish the failure event first, then delete the request message.

## 7. End-to-End Event Flow

The following sequence describes the successful event-driven workflow.

**Step 1 — Job Creation**

The Core Backend validates the submitted sources and creates the corresponding processing tasks.

**Step 2 — Task Distribution**

The Job Orchestrator publishes the required processing events:

- `cv.extract.requested`
- `github.analyze.requested`
- `linkedin.extract.requested`

Only events corresponding to provided sources are published.

**Step 3 — AI Processing**

Each processing service consumes its request, retrieves the required input, generates structured JSON, and stores the result in S3.

**Step 4 — Processing Completion**

Each processing service publishes `processing.completed`.

The Core Backend consumes the events, retrieves the results, and updates the corresponding task statuses.

**Step 5 — Profile Aggregation**

When every requested task is terminal and the CV task has completed, the Job Orchestrator invokes the Profile Aggregation Module internally.

The unified profile is stored in PostgreSQL.

**Step 6 — Website Generation**

The Profile Aggregator publishes `profile.ready`.

The Website Service consumes the event, generates the website draft, and persists it.

**Step 7 — Website Generation Completion**

The Website Service publishes `website.generated`.

The Core Backend updates the job status and enables website preview.

**Step 8 — Website Publishing**

The user explicitly approves the website and calls the publish endpoint, which returns `202 Accepted`.

The Website Service emits `website.publish.requested` through its outbox. The Website Publisher consumes it, renders and uploads the site, and emits `website.published` (or `website.failed` with `stage = WEBSITE_PUBLISHING`).

**Step 9 — Final Status**

The Core Backend consumes `website.published` and makes the public website URL available to the Frontend, which learns it by polling the job status.

**Failure Path**

- A permanent failure in an AI service publishes `processing.failed`. A CV failure fails the job; a GitHub or LinkedIn failure adds a warning and the job continues from the CV.
- A website generation failure publishes `website.failed` (job `FAILED`). A publishing failure publishes `website.failed` with `stage = WEBSITE_PUBLISHING` and returns the job to `PREVIEW_READY`.
- A message that keeps failing lands in its DLQ and the Core DLQ listener marks the job failed with `RETRIES_EXHAUSTED`.
- A Core watchdog fails jobs stuck in a non-terminal state (`TIMEOUT`).

## 8. Message Delivery and Processing Rules

### 8.1 At-Least-Once Delivery

Amazon SQS Standard may deliver the same message more than once.

Consumers must not assume exactly-once processing.

All services must implement idempotent message handling.

**Examples**

- Duplicate `cv.extract.requested` events must not create multiple final results for the same task.
- Duplicate `processing.completed` events must not trigger repeated profile aggregation.
- Duplicate `profile.ready` events must not create multiple websites for the same generation operation.
- Duplicate `website.publish.requested` and `website.published` events must not cause repeated publication or repeated state changes.

### 8.2 Message Ordering

SQS Standard does not guarantee strict message ordering.

Processing results may arrive in any order.

The Job Orchestrator must use persisted task statuses rather than message arrival order to determine when aggregation can begin.

Consumers must also reject state transitions that would incorrectly overwrite newer durable states.

### 8.3 Message Acknowledgement

A message must be deleted from its SQS queue only after its required processing has completed successfully.

When processing includes publishing another event, the implementation must account for the possibility that the outgoing publication fails after local state has been stored.

Core uses a transactional outbox for the events it publishes (`cv.extract.requested`, `github.analyze.requested`, `linkedin.extract.requested`, `profile.ready`), and the Website Service uses one for `website.publish.requested`: the state change and an `outbox` row are written in one transaction, and a relay publishes and marks rows sent. A relay crash can publish an event twice, which consumers already tolerate. Services that publish `processing.completed`, `processing.failed` and the website result events publish first and delete the request message afterwards; if publishing fails the message is redelivered.

### 8.4 Result Storage

Original documents and large extraction results must not be embedded in SQS messages.

For source processing:

1. Core Backend stores input documents in private S3 storage.
2. Processing services retrieve the documents using the provided object keys.
3. Processing services write validated JSON results to private S3 storage.
4. Completion events contain references to those results.
5. Core Backend retrieves and validates the structured output.

S3 bucket names are configured through environment-specific application configuration.

### 8.5 Validation

Consumers must validate incoming messages against their corresponding event schemas before processing.

Validation includes:

- Required fields.
- Field types and enum values.
- Supported schema version.
- Valid identifier formats.
- Valid storage references.
- Correct event type for the consuming service.

The Core Backend additionally verifies that completion events correspond to existing jobs and tasks.

An SQS message must not be treated as proof of user authorization.

A message that fails validation (malformed JSON, unsupported `schemaVersion`, missing required field, unknown `jobId`) is a poison message. It is not processed, no failure event is published (its identifiers cannot be trusted), and it is left to reach `maxReceiveCount` and move to the DLQ.

## 9. Event Ownership and Versioning

Every event has a defined producer responsible for maintaining the contract.

| Event | Contract Owner |
| --- | --- |
| cv.extract.requested | Core Backend |
| github.analyze.requested | Core Backend |
| linkedin.extract.requested | Core Backend |
| processing.completed | Shared contract — Core Backend coordinates |
| profile.ready | Core Backend |
| website.generated | Website Service |
| website.publish.requested | Website Service |
| website.published | Website Service |
| processing.failed | Shared contract — Core Backend coordinates |
| website.failed | Website Service |

**Versioning Rules**

- MVP events use `schemaVersion: 1`.
- Compatible schema additions may preserve the same major version.
- Breaking changes require a new contract version and coordinated consumer migration.
- Consumers must reject or explicitly handle unsupported major versions.
- Changes must be validated against the shared contract definitions before merging.

Machine-readable event contracts are maintained using JSON Schema and AsyncAPI in the shared GitHub `contracts/` directory.
