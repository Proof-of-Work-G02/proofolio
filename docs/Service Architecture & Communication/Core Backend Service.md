# Core Backend Service

**Service Type:** Backend Microservice  
**Main Responsibility:** User authentication, data ingestion, job orchestration and unified profile aggregation

**Scope:** Happy Flow only

---

## 1. Purpose

The Core Backend Service acts as the central entry point and orchestration component of the application.

It is responsible for authenticating users, receiving portfolio data sources, coordinating asynchronous AI processing tasks and combining extracted information into a unified user profile.

The service communicates with the Frontend through HTTP REST APIs and with the AI Processing Services through Amazon SQS.

Once all requested AI processing tasks have been completed, the Core Backend Service aggregates the extracted information and triggers website generation.

It also provides the Frontend with access to website preview, publishing and the "My sites" list by communicating with the Website Service.

The service contains four internal modules:

- **Authentication Module**
- **Ingestion Module**
- **Job Orchestration Module**
- **Profile Aggregation Module**

All four modules belong to the same logical and deployable service.

---

## 2. Internal Modules

### 2.1 Authentication Module

Responsible for user authentication and user identity management.

**Responsibilities:**

- Support user authentication through Google OAuth and GitHub OAuth.
- Handle OAuth authentication flows and callbacks.
- Create user records after successful authentication.
- Manage authenticated user sessions: a random session id (stored hashed in `sessions`) carried in the httpOnly, host-only `pf_session` cookie.
- Provide user identity information to other internal modules.
- Validate authentication for protected API endpoints.
- Store no OAuth provider tokens: sign-in only establishes identity.

**Inputs:**

- OAuth authentication request
- OAuth authorization response
- User identity information from the OAuth provider

**Outputs:**

- Authenticated user identity
- User session cookie
- `userId`

### 2.2 Ingestion Module

Responsible for receiving and validating the data sources required to generate a personal portfolio website.

**Responsibilities:**

- Receive CV files uploaded through the Frontend.
- Receive the user's GitHub username or profile URL and normalize it to `githubUsername`.
- Receive the user-exported LinkedIn profile PDF (`linkedinPdf`) with user consent. A LinkedIn URL alone is not accepted in the MVP.
- Validate incoming files and source information, including file type and size limits.
- Upload CV files and other uploaded source files to a private Amazon S3 bucket.
- Prepare source references for the Job Orchestration Module.
- Pass the selected website template identifier to the orchestration process.

**Inputs:**

- Authenticated `userId`
- CV file
- GitHub profile URL or username, if provided
- LinkedIn profile PDF, if provided
- `templateId`

**Outputs:**

- Validated source information
- S3 object references for uploaded files
- List of requested processing sources
- Selected `templateId`

### 2.3 Job Orchestration Module

Responsible for coordinating asynchronous AI processing and tracking job execution.

**Responsibilities:**

- Create processing jobs after successful data ingestion.
- Create individual tasks for the requested data sources.
- Dispatch extraction and analysis tasks to dedicated Amazon SQS queues.
- Track the processing status of each task.
- Consume `processing.completed` events from the `processing-results` queue.
- Store the `resultS3Key` of each completed extraction result (and, optionally, a validated JSONB copy) in `extraction_results`.
- Determine when all requested processing tasks have completed.
- Trigger the Profile Aggregation Module.
- Track website generation and publication events: `website.generated` sets the job `PREVIEW_READY`, and `website.published` sets it `PUBLISHED`.
- Consume `processing.failed` and `website.failed`, run the DLQ listener and the job watchdog, and offer user-initiated retry (see section 7a).
- Provide job status information to the Frontend.
- Enforce per-user request, upload and generation limits (`429 RATE_LIMITED`).

**Inputs:**

- `userId`
- Validated source references
- `templateId`
- Processing completion events
- Website generation and publishing completion events

**Outputs:**

- `jobId`
- Processing task identifiers
- SQS processing requests
- Updated job and task statuses
- Profile aggregation trigger

**Processing Rules:**

- Only tasks corresponding to provided data sources are created.
- CV extraction is initiated for the uploaded CV.
- GitHub and LinkedIn processing are initiated only when their respective sources are provided.
- Processing tasks can execute independently and concurrently.
- Profile aggregation starts when every requested task is terminal (`COMPLETED` or `FAILED`) and the CV task is `COMPLETED`. A failed optional source becomes a job warning.

### 2.4 Profile Aggregation Module

Responsible for combining AI extraction results into a unified user profile.

**Responsibilities:**

- Receive an internal aggregation request from the Job Orchestration Module.
- Retrieve completed extraction results from the appropriate storage.
- Combine CV, GitHub and LinkedIn information into a unified data structure.
- Normalize extracted information into a consistent profile format.
- Identify and consolidate duplicated information.
- Store the unified profile in PostgreSQL using JSONB.
- Publish a `profile.ready` message to Amazon SQS through the transactional outbox.

**Inputs:**

- `jobId`
- `userId`
- Completed extraction results
- `templateId`

**Outputs:**

- Unified profile JSON
- `profileId`
- `profile.ready` event

**Important:** Profile aggregation is an internal operation within the Core Backend Service. It does not require HTTP communication between separate services.

---

## 3. Incoming Communication

The Core Backend Service receives synchronous HTTP requests from the Frontend, OAuth responses from authentication providers and asynchronous events from Amazon SQS.

| Source | Technology | Purpose |
| --- | --- | --- |
| Frontend | HTTP REST | User authentication and source submission |
| Frontend | HTTP REST | Retrieve job processing status |
| Frontend | HTTP REST | Request website preview, publishing and the "My sites" list |
| Frontend | HTTP REST | Delete the signed-in user's data (`DELETE /api/me`) |
| Google / GitHub | OAuth 2.0 / HTTPS | Complete authentication flows |
| CV Extraction Service | Amazon SQS (`processing-results`) | Receive CV extraction completion |
| GitHub Analysis Service | Amazon SQS (`processing-results`) | Receive GitHub analysis completion |
| LinkedIn Extraction Service | Amazon SQS (`processing-results`) | Receive LinkedIn extraction completion |
| Website Service | Amazon SQS (`processing-results`) | Receive website generation, publishing and failure events |

**Communication Flow:**

1. The user authenticates through Google or GitHub.
2. The Frontend submits the required portfolio information.
3. The Ingestion Module validates and stores uploaded files.
4. The Job Orchestration Module creates and distributes processing tasks.
5. AI Processing Services return completion events through Amazon SQS.
6. The Job Orchestration Module processes the results and initiates profile aggregation.
7. The Profile Aggregation Module creates the unified profile.
8. The Core Backend Service receives website generation completion and provides preview access.
9. The user approves and publishes the generated website through the Core Backend API (`202`); the frontend polls the job status until it is `PUBLISHED`.

---

## 4. Outgoing Communication

| Destination | Protocol / Technology | Purpose |
| --- | --- | --- |
| Google / GitHub OAuth | HTTPS / OAuth 2.0 | Authenticate users |
| PostgreSQL | SQL | Store users, sessions, jobs, tasks, extraction results and unified profiles |
| Amazon S3 | AWS SDK / S3 API | Store uploaded CVs and other source files |
| Amazon SQS (`cv-extraction`) | AWS SDK / SQS API | Send CV extraction requests |
| Amazon SQS (`github-analysis`) | AWS SDK / SQS API | Send GitHub analysis requests |
| Amazon SQS (`linkedin-extraction`) | AWS SDK / SQS API | Send LinkedIn extraction requests |
| Amazon SQS (`website-generation`) | AWS SDK / SQS API | Send `profile.ready` messages |
| Website Service | HTTP REST (HMAC-signed) | Request website preview, publishing, generation retry and the sites list |

**Important Considerations:**

- PostgreSQL is the main database for application and processing data.
- Amazon S3 stores original uploaded files in private storage.
- Amazon SQS is used for asynchronous processing communication.
- Each AI Processing Service consumes tasks from its dedicated SQS queue.
- The Core Backend Service consumes processing results from a shared SQS queue.
- Large files and datasets are stored outside SQS messages and referenced by identifiers or storage locations.
- The Website Service is responsible for website generation, draft storage and publishing.
- The Core Backend Service does not generate or host portfolio websites.

---

## 5. Data Ownership

The Core Backend Service owns user-related, ingestion-related and processing-related data in PostgreSQL.

### 5.1 PostgreSQL

**Table:** `users`

Stores application user information.

| Field | Description |
| --- | --- |
| `id` | Unique user identifier |
| `email` | User email address |
| `name` | User display name |
| `created_at` | Account creation timestamp |

**Table:** `oauth_accounts`

Stores connections between application users and external authentication providers. No provider tokens are stored.

| Field | Description |
| --- | --- |
| `id` | Unique OAuth account identifier |
| `user_id` | Associated application user |
| `provider` | Google / GitHub |
| `provider_user_id` | User identifier from the provider |

**Table:** `sessions`

Stores signed-in sessions.

| Field | Description |
| --- | --- |
| `id` | Random session id, stored hashed; the plain value is only in the `pf_session` cookie |
| `user_id` | Session owner |
| `created_at` | Creation timestamp |
| `expires_at` | Expiry timestamp |
| `last_seen_at` | Last request timestamp |

**Table:** `jobs`

Stores the overall processing job.

| Field | Description |
| --- | --- |
| `id` | Unique job identifier |
| `user_id` | Job owner |
| `template_id` | Selected website template |
| `status` | Overall processing status: `QUEUED`, `PROCESSING`, `AGGREGATING`, `GENERATING`, `PREVIEW_READY`, `PUBLISHING`, `PUBLISHED`, `FAILED` (allowed transitions: section 7a) |
| `created_at` | Job creation timestamp |
| `updated_at` | Last status update timestamp |
| _failure columns_ | `failed_stage`, `error_code`, `error_message`, `failed_at`, `status_changed_at`, `warnings` (see Failure-handling columns below) |

**Table:** `job_tasks`

Stores individual AI processing tasks.

| Field | Description |
| --- | --- |
| `id` | Unique task identifier |
| `job_id` | Associated processing job |
| `source_type` | CV / GITHUB / LINKEDIN |
| `status` | Task processing status: `PENDING`, `COMPLETED`, `FAILED` (there is no task-level `PROCESSING`) |
| `created_at` | Task creation timestamp |
| `completed_at` | Task completion timestamp |
| _failure columns_ | `attempt`, `error_code`, `error_message`, `failed_at` (see Failure-handling columns below) |

**Table:** `extraction_results`

Stores structured extraction results returned by AI Processing Services.

| Field | Description |
| --- | --- |
| `id` | Unique extraction result identifier |
| `job_task_id` | Associated processing task |
| `source_type` | Original data source |
| `result_s3_key` | S3 object key of the stored extraction result, relative to the `extraction-results` bucket (from `resultS3Key`) |
| `result_data` | Optional validated JSONB copy of the extraction output, to simplify aggregation |
| `created_at` | Result creation timestamp |

Extraction results live in S3; `result_s3_key` is required and `result_data` is an optional JSONB copy. `UNIQUE(job_task_id)` gives one authoritative result per task.

**Table:** `profiles`

Stores the unified user profile produced by the Profile Aggregation Module.

| Field | Description |
| --- | --- |
| `id` | Unique profile identifier |
| `user_id` | Profile owner |
| `job_id` | Associated processing job |
| `profile_data` | Aggregated profile information (JSONB) |
| `created_at` | Profile creation timestamp |

`profile_data` follows the `UnifiedProfile` contract (Shared Data Contracts §8). It does not repeat `profileId`, `jobId` or `userId`; those are the columns `id`, `job_id` and `user_id`. `profiles.user_id` is a foreign key to `users.id`. `UNIQUE(job_id)` gives one authoritative profile per job. Other constraints are listed in Database Architecture §7.3.

**Failure-handling columns**

| Table | Columns |
| --- | --- |
| `jobs` | `failed_stage`, `error_code`, `error_message`, `failed_at`, `status_changed_at`, `warnings` (JSONB array, default `[]`) |
| `job_tasks` | `attempt` (integer, default 1), `error_code`, `error_message`, `failed_at` |

**Table:** `outbox`

| Field | Description |
| --- | --- |
| `id` | Unique outbox row identifier |
| `queue` | Destination queue |
| `event_type` | Event name |
| `payload` | Event JSON (JSONB) |
| `created_at` | Creation timestamp |
| `sent_at` | When the relay published it (NULL until sent) |

**Table:** `dlq_seen`

| Field | Description |
| --- | --- |
| `dlq_name` | DLQ the message came from |
| `message_id` | SQS message id (together with `dlq_name`, the primary key) |
| `seen_at` | When the listener processed it |

The exact SQL types, constraints, relationships and indexes are defined in Database Architecture.

### 5.2 Amazon S3

Stores original uploaded files required for AI processing.

**Example structure:**

```
portfolio-uploads/
  user-123/
    job-456/
      cv.pdf
      linkedin-profile.pdf
```

The uploaded files remain private and are accessed only by authorized application components.

The Core Backend Service does not own the `websites` table or published website files. Those belong to the Website Service.

---

## 6. Events & API Endpoints

### 6.1 Published Events

**Event:** `cv.extract.requested`

**Producer:** Job Orchestration Module  
**Consumer:** CV Extraction Service  
**Technology:** Amazon SQS Standard  
**Queue:** `cv-extraction`

Triggers CV extraction using the uploaded document reference.

**Event:** `github.analyze.requested`

**Producer:** Job Orchestration Module  
**Consumer:** GitHub Analysis Service  
**Technology:** Amazon SQS Standard  
**Queue:** `github-analysis`

Triggers GitHub profile and repository analysis. The event carries the username only; no token or token reference.

**Event:** `linkedin.extract.requested`

**Producer:** Job Orchestration Module  
**Consumer:** LinkedIn Extraction Service  
**Technology:** Amazon SQS Standard  
**Queue:** `linkedin-extraction`

Triggers extraction from the LinkedIn data supplied by the user.

**Event:** `profile.ready`

**Producer:** Profile Aggregation Module  
**Consumer:** Website Generator Module  
**Technology:** Amazon SQS Standard  
**Queue:** `website-generation`

Triggered after the unified user profile has been successfully created and stored in PostgreSQL.

### 6.2 Consumed Events

**Event:** `processing.completed`

**Producer:** AI Processing Services  
**Consumer:** Job Orchestration Module  
**Technology:** Amazon SQS Standard  
**Queue:** `processing-results`

Indicates that an AI processing task has completed and its extraction result is available.

The Job Orchestration Module uses the job and task identifiers to track completion and determine when profile aggregation can begin.

**Event:** `website.generated`

**Producer:** Website Generator Module  
**Consumer:** Job Orchestration Module  
**Technology:** Amazon SQS Standard  
**Queue:** `processing-results`

Indicates that the generated website draft is ready for preview.

**Event:** `website.published`

**Producer:** Website Publisher Module  
**Consumer:** Core Backend Service  
**Technology:** Amazon SQS Standard  
**Queue:** `processing-results`

Indicates that the website has been successfully published. The consumer sets the job to `PUBLISHED`.

#### Event Payload Summary

| Event | Queue | Direction for Core Backend | Business fields (besides common metadata) |
| --- | --- | --- | --- |
| `cv.extract.requested` | `cv-extraction` | Publishes | `taskId`, `userId`, `cvS3Key` |
| `github.analyze.requested` | `github-analysis` | Publishes | `taskId`, `userId`, `githubUsername` |
| `linkedin.extract.requested` | `linkedin-extraction` | Publishes | `taskId`, `userId`, `linkedinS3Key` |
| `processing.completed` | `processing-results` | Consumes | `taskId`, `sourceType`, `status` (`COMPLETED`), `resultS3Key` |
| `profile.ready` | `website-generation` | Publishes | `userId`, `profileId`, `templateId` |
| `website.generated` | `processing-results` | Consumes | `userId`, `profileId`, `websiteId`, `status` (`PREVIEW_READY`) |
| `website.published` | `processing-results` | Consumes | `userId`, `websiteId`, `slug`, `status` (`PUBLISHED`), `url` |
| `processing.failed` | `processing-results` | Consumes | `taskId`, `userId`, `sourceType`, plus `stage`, `errorCode`, `errorMessage`, `retryable`, `attempts`, optional `diagnosticsS3Key` |
| `website.failed` | `processing-results` | Consumes | `userId`, `profileId`, optional `websiteId`, plus `stage`, `errorCode`, `errorMessage`, `retryable`, `attempts`, optional `diagnosticsS3Key` |

The `website.publish.requested` event (queue `website-publishing`) is produced and consumed inside the Website Service; Core only starts it through the internal publish call and observes the result through `website.published` and `website.failed`.

S3 keys (`cvS3Key`, `linkedinS3Key`, `resultS3Key`) are relative to their configured buckets; consumers must not prepend a bucket name.

### 6.3 HTTP API Endpoints

The following endpoints describe the Core Backend API responsibilities. Routes, request bodies and response schemas are defined in HTTP API Contracts.

| Method | Endpoint / Operation | Description |
| --- | --- | --- |
| OAuth | `/auth/*` | Initiate and complete Google/GitHub authentication; set and clear the `pf_session` cookie |
| `POST` | `/api/jobs` | Submit portfolio sources and create a processing job |
| `GET` | `/api/jobs/{jobId}` | Retrieve processing status |
| `GET` | `/api/websites/{websiteId}/preview` | Retrieve the generated website preview through Website Service |
| `POST` | `/api/websites/{websiteId}/publish` | Forward an authorized website publishing request (returns `202`) |
| `POST` | `/api/jobs/{jobId}/retry` | Retry a failed job (valid only for a `FAILED` job with `retryable = true`) |
| `GET` | `/api/websites` | List the signed-in user's websites ("My sites") |
| `DELETE` | `/api/me` | Delete the user's data: sessions, OAuth accounts, jobs, tasks, results, profiles, websites, and the S3 objects under the user's keys |

**POST — Create Processing Job**

The Frontend submits the user's portfolio data, including the CV and selected template.

The Ingestion Module validates the data and stores uploaded files in Amazon S3.

The Job Orchestration Module creates the job and dispatches processing requests to the appropriate SQS queues.

The request is `multipart/form-data` with `cv` (file, required), `githubUsername` (optional), `linkedinPdf` (file, optional) and `templateId` (required). The Core Backend Service responds **202 Accepted** with `jobId`, `status` (`QUEUED`) and the list of tasks (`taskId`, `sourceType`, `status`).

**GET — Processing Status**

The Frontend uses `jobId` to retrieve the current processing status.

The Core Backend Service retrieves the job information from PostgreSQL. The response includes `warnings` for skipped optional sources and, when the job is `FAILED`, an `error` object (`code`, `message`, `stage`, `retryable`). When the job is `PUBLISHED` it includes `slug` and `url`.

Once the website is generated, the Frontend can obtain the website identifier and request its preview.

**GET — Website Preview**

The Core Backend Service validates the authenticated user's access and forwards the request to the Website Service.

The Website Service returns the generated draft required for preview.

**POST — Publish Website**

The Core Backend Service receives the user's selected subdomain slug (`{ "slug": "alex-popescu" }`), validates user authorization, moves the job to `PUBLISHING` and forwards the publishing request to the Website Service, which answers `202 Accepted`. Publishing is idempotent for the same website and slug. The frontend polls the job status until it is `PUBLISHED`, or `PREVIEW_READY` after a failed publish.

If the requested slug is already taken, the Website Service returns `409 Conflict`, which is propagated to the Frontend.

**GET — My sites**

Returns the signed-in user's websites (status, slug, public URL) from the Website Service.

**DELETE — My data**

Removes the user's records and stored files (and unpublishes and removes published site files) so that no personal data remains.

---

## 7. Core Backend Service Happy Flow

1. The user authenticates through Google or GitHub OAuth.
2. The Authentication Module identifies the authenticated user and sets the session cookie.
3. The Frontend submits the CV, optional GitHub and LinkedIn sources, and selected website template.
4. The Ingestion Module validates the provided data and uploads files to private Amazon S3 storage.
5. The Job Orchestration Module creates a job and the required processing tasks in PostgreSQL.
6. The Job Orchestration Module sends processing requests to the corresponding Amazon SQS queues:
    - `cv-extraction`
    - `github-analysis`
    - `linkedin-extraction`
7. The AI Processing Services independently consume and process their assigned tasks.
8. Each completed AI service sends a `processing.completed` message to the Amazon SQS `processing-results` queue.
9. The Job Orchestration Module consumes the completion messages, stores the extraction results or their references, and updates task statuses.
10. When all requested tasks are terminal and the CV task is completed, the Job Orchestration Module triggers the Profile Aggregation Module internally.
11. The Profile Aggregation Module retrieves the extraction results, normalizes and combines them into a unified profile.
12. The unified profile is stored in PostgreSQL.
13. The Profile Aggregation Module sends a `profile.ready` message to the Amazon SQS `website-generation` queue.
14. The Website Service consumes the message and generates the website draft.
15. The Website Service sends a `website.generated` message to the Amazon SQS `processing-results` queue.
16. The Core Backend Service processes the event and makes the generated website available for frontend preview.
17. The user reviews the preview and selects Publish.
18. The Core Backend Service validates the request, moves the job to `PUBLISHING` and forwards the publishing request to the Website Service through HTTP REST; the response is `202`.
19. The Website Service renders and publishes the website asynchronously and sends a `website.published` message to the Amazon SQS `processing-results` queue.
20. The Core Backend Service sets the job to `PUBLISHED`; the polling Frontend receives the published website URL.

---

## 7a. Failure Handling

**Aggregation rule.** Aggregation starts when every requested task is terminal (`COMPLETED` or `FAILED`) **and the CV task is `COMPLETED`**. The CV is the required source. A failed GitHub or LinkedIn task does not fail the job: it is left out of the profile and recorded in `jobs.warnings`. A failed CV task fails the job.

**Failure events consumed.** `processing.failed` marks the task `FAILED` and stores `error_code`, `error_message`, `failed_at`. `website.failed` with `stage = WEBSITE_GENERATION` fails the job; with `stage = WEBSITE_PUBLISHING` it returns the job from `PUBLISHING` to `PREVIEW_READY` without failing it. Core moves the job to `PUBLISHING` when it forwards a publish request.

**Allowed job transitions** (applied only with a compare-and-set; zero changed rows means a duplicate or stale event and the message is acknowledged):

```
QUEUED -> PROCESSING -> AGGREGATING -> GENERATING -> PREVIEW_READY -> PUBLISHING -> PUBLISHED
FAILED is reachable from any non-terminal state.
PUBLISHING -> PREVIEW_READY when publishing fails (the user may retry).
```

From `PROCESSING` a job fails only for a CV failure, a timeout, or when no required task can complete. `PUBLISHED` and `FAILED` accept no further transitions except the user-initiated retry.

**Idempotent aggregation.** Aggregation is guarded by the transition `PROCESSING → AGGREGATING`; only the caller that changes one row proceeds. The profile insert uses `UNIQUE(profiles.job_id)` with `ON CONFLICT DO NOTHING`.

**Transactional outbox.** `profile.ready` is published through an outbox: the profile row, the `AGGREGATING → GENERATING` transition and an `outbox` row are written in one transaction. A relay publishes from the outbox and marks rows sent. The same outbox is used for `cv.extract.requested`, `github.analyze.requested` and `linkedin.extract.requested`. A relay crash may publish an event twice; the Website Service handles that.

**Watchdog.** A scheduled job checks `jobs.status_changed_at` and fails jobs that stay in a non-terminal state too long, with `errorCode = TIMEOUT`. Thresholds: `QUEUED` 5 min, `PROCESSING` 30 min, `AGGREGATING` 5 min, `GENERATING` 30 min, `PUBLISHING` 10 min.

**DLQ listener.** One listener in Core reads all six DLQs (including `website-publishing-dlq`). For each message it parses `jobId` and, where present, `taskId` or `profileId`, calls the same internal "mark failed" operation with `errorCode = RETRIES_EXHAUSTED` and `retryable = true`, records the DLQ `messageId` in `dlq_seen`, and leaves the message in the DLQ. A poison message with no usable ids is only logged and alarmed. Core's own queue handling is also bounded: `processing-results` has `maxReceiveCount` 5 and visibility timeout 1 min.

**Stale and out-of-order events**

| Situation | Behavior |
| --- | --- |
| `processing.completed` for a task already `FAILED` | Ignored and logged |
| `processing.failed` for an optional source after aggregation started | Task marked `FAILED`, warning added, aggregation not redone |
| `processing.failed` for a task already `COMPLETED` | Ignored and logged |
| Any event for a job already `FAILED` | Ignored, except `website.published` for a website that really was published (recorded; the job moves to `PUBLISHED` only if the transition is allowed) |
| Event for an unknown `jobId` or `taskId` | Logged, then the message goes to the DLQ |
| Event with an older `attempt` than the task's current one | Ignored |

**Retry.** `POST /api/jobs/{jobId}/retry` is valid only for a `FAILED` job whose failure is `retryable`. A source failure resets the failed tasks to `PENDING`, increments `job_tasks.attempt` and re-publishes the request events with the new `attempt`. A website generation failure moves the job `FAILED → GENERATING`, resets the **same** website row through the Website Service and re-publishes `profile.ready` for the same `profileId`. See HTTP API Contracts §3.5.

**Observability.** Log every failure with `jobId`, `taskId`, `eventId`, `stage`, `errorCode`, `attempt` and `receiveCount` (no personal data). Alarm on any DLQ message, on watchdog timeouts above a threshold and on `processing-results` queue age. Add `failed-jobs` to the operational dashboard.

## 8. Architectural Notes

- The Core Backend Service is one deployable service containing four internal modules.
- Internal modules communicate through direct application-level calls rather than separate service APIs.
- Amazon SQS Standard is used for asynchronous processing communication.
- SQS message consumers must support idempotent processing because duplicate deliveries are possible.
- The Job Orchestration Module coordinates only the processing tasks corresponding to the sources submitted by the user.
- Large files and datasets are stored in S3 or PostgreSQL rather than directly inside SQS messages.
- The Profile Aggregation Module produces a single unified profile used by the Website Service.
- The Core Backend Service is the API entry point for the Frontend.
- Website generation and publishing remain the responsibility of the Website Service.
- Authentication credentials and access tokens must not be included in SQS event payloads. No OAuth provider tokens are stored; GitHub analysis uses one server-side token.
- The session cookie is host-only (no `Domain` attribute), so published user sites never receive it.
