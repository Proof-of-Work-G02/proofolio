# HTTP API Contracts

**Project:** AI-Powered Personal Website Generator  
**Scope:** MVP / Happy Flow  
**Communication Protocol:** HTTP/HTTPS REST

## 1. Purpose

This document defines the HTTP communication contracts between the application's components.

It specifies the available endpoints, request and response structures, authentication requirements, validation rules, HTTP status codes, and service responsibilities.

The objective is to establish consistent interfaces that allow the Frontend, Core Backend Service, and Website Service to be developed and tested independently.

Detailed asynchronous communication is documented separately in **SQS Event Contracts**, while reusable JSON structures are defined in **Shared Data Contracts**.

## 2. HTTP Communication Architecture

The application uses two HTTP communication boundaries.

### 2.1 Frontend → Core Backend Service

The Core Backend Service is the single entry point for frontend application requests.

Responsibilities:

- Authenticate and authorize incoming requests.
- Receive and validate submitted user data.
- Create processing jobs.
- Provide job status information.
- Retrieve website previews.
- Forward authorized publishing requests.

The Frontend must not communicate directly with internal processing services or the Website Service.

### 2.2 Core Backend Service → Website Service

The Core Backend Service communicates with the Website Service through internal REST endpoints.

This communication is used for:

- Retrieving generated website drafts.
- Publishing approved websites under unique subdomains.

Internal endpoints must not be publicly accessible.

### 2.3 AI Processing Services

The CV Extraction, GitHub Analysis, and LinkedIn Extraction services do not expose HTTP endpoints as part of the MVP Happy Flow.

They communicate asynchronously through Amazon SQS and exchange large processing results through private Amazon S3 storage.

## 3. Public API — Frontend ↔ Core Backend

**Base path:** `/api`

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/jobs` | Submit portfolio sources and create a processing job |
| GET | `/api/jobs/{jobId}` | Retrieve processing job status |
| GET | `/api/websites/{websiteId}/preview` | Retrieve generated website preview |
| POST | `/api/websites/{websiteId}/publish` | Publish an approved website (asynchronous) |
| POST | `/api/jobs/{jobId}/retry` | Retry a failed job |
| GET | `/api/websites` | List the signed-in user's websites ("My sites") |

All six endpoints require an authenticated user.

### 3.1 POST /api/jobs

**Purpose**

Creates a new portfolio generation job based on the user's submitted data sources and selected website template.

**Content-Type:** `multipart/form-data`

**Request Parameters**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| cv | File | Yes | User's CV document |
| githubUsername | String | No | GitHub username |
| linkedinPdf | File | No | User-exported LinkedIn profile PDF |
| templateId | String | Yes | Selected website template identifier |

**Processing Behavior**

1. Validate the authenticated user and submitted parameters.
2. Validate the uploaded documents.
3. Store uploaded files in private Amazon S3 storage.
4. Create a processing job in PostgreSQL.
5. Create individual tasks for the submitted sources.
6. Dispatch processing requests to the corresponding SQS queues.
7. Return the processing job identifier.

Only the services corresponding to submitted sources are invoked.

**Success Response — 202 Accepted**

```json
{
  "jobId": "job-456",
  "status": "QUEUED",
  "tasks": [
    {
      "taskId": "task-789",
      "sourceType": "CV",
      "status": "PENDING"
    },
    {
      "taskId": "task-790",
      "sourceType": "GITHUB",
      "status": "PENDING"
    }
  ]
}
```

The response confirms that the processing job was accepted, not that extraction or website generation has finished.

### 3.2 GET /api/jobs/{jobId}

**Purpose**

Retrieves the current processing status of a portfolio generation job.

**Path Parameters**

| Parameter | Type | Description |
| --- | --- | --- |
| jobId | String | Unique processing job identifier |

**Processing Behavior**

1. Authenticate the requesting user.
2. Verify ownership of the requested job.
3. Retrieve job and task information from PostgreSQL.
4. Return the current processing status.

**Success Response — 200 OK**

```json
{
  "jobId": "job-456",
  "status": "PREVIEW_READY",
  "tasks": [
    {
      "taskId": "task-789",
      "sourceType": "CV",
      "status": "COMPLETED"
    },
    {
      "taskId": "task-790",
      "sourceType": "GITHUB",
      "status": "COMPLETED"
    }
  ],
  "websiteId": "website-456",
  "warnings": [
    {
      "sourceType": "LINKEDIN",
      "errorCode": "SOURCE_UNREADABLE",
      "message": "The LinkedIn PDF could not be read. Your site was built from your CV."
    }
  ]
}
```

**Job Statuses**

| Status | Description |
| --- | --- |
| QUEUED | Job created and waiting for processing |
| PROCESSING | Source extraction or analysis in progress |
| AGGREGATING | Extracted information is being combined |
| GENERATING | Website draft is being generated |
| PREVIEW\_READY | Generated website is ready for preview |
| PUBLISHING | Publication has been requested and is in progress |
| PUBLISHED | Website successfully published |
| FAILED | Job could not complete successfully |

The `websiteId` becomes available after website generation.

- Task `status` is `PENDING`, `COMPLETED` or `FAILED`.
- `warnings` is always present (empty by default) and lists skipped optional sources (Shared Data Contracts §3.4). A job with warnings in `PREVIEW_READY` is a success.
- When the job is `FAILED`, the response contains `error: { code, message, stage, retryable }` (Shared Data Contracts §3.3).
- A failed publish returns the job from `PUBLISHING` to `PREVIEW_READY`; it is not `FAILED`.

The Frontend can poll this endpoint to track progress.

### 3.3 GET /api/websites/{websiteId}/preview

**Purpose**

Retrieves the generated website draft for authenticated user preview.

**Path Parameters**

| Parameter | Type | Description |
| --- | --- | --- |
| websiteId | String | Generated website identifier |

**Processing Behavior**

1. Authenticate the user.
2. Validate website ownership.
3. Forward the request to the Website Service.
4. Retrieve the generated draft.
5. Return the draft data to the Frontend.

**Success Response — 200 OK**

The response is `WebsitePreview` (Shared Data Contracts §9.3): the stored draft (`schemaVersion`, `content`) together with `websiteId`, `profileId`, `templateId` and `status` taken from the `websites` columns.

The representation contains:

- Website identifier.
- Selected template identifier.
- Generated website content.
- Structured sections required for rendering.

The website remains unpublished, and no public subdomain is required during preview.

### 3.4 POST /api/websites/{websiteId}/publish

**Purpose**

Publishes a generated website after explicit user approval. Publishing is asynchronous.

**Content-Type:** `application/json`

**Request Body**

```json
{
  "slug": "alex-popescu"
}
```

**Processing Behavior**

1. Authenticate the user.
2. Verify website ownership.
3. Forward the authorized request to the Website Service.
4. Validate the selected slug.
5. Reserve the slug using PostgreSQL uniqueness enforcement.
6. Set the website and job to `PUBLISHING` and queue the `website.publish.requested` event (outbox).
7. Return `202 Accepted` immediately. Rendering, upload and the `website.published` event happen afterwards in the Website Service.

The frontend polls `GET /api/jobs/{jobId}` until the job is `PUBLISHED` (the response then includes `slug` and `url`) or back to `PREVIEW_READY` after a failure.

**Success Response — 202 Accepted**

```json
{
  "websiteId": "website-456",
  "slug": "alex-popescu",
  "status": "PUBLISHING"
}
```

A repeat for the same website and slug returns `202` while `PUBLISHING`, and `200 OK { websiteId, slug, status: "PUBLISHED", url }` once published.

**Slug takeover:** a user who already owns the slug through an older website of their own may publish a newer website to it; the slug moves in one transaction and the old website becomes `UNPUBLISHED`.

**Conflict Response — 409 Conflict**

Returned (`SLUG_TAKEN`) when the requested subdomain is already assigned to another website or user. Returned (`SLUG_CONFLICT`) when the website is already published under a different slug (no renaming in version 1).

Subdomain uniqueness must be enforced through a PostgreSQL `UNIQUE` constraint.

**Publish failure**

While publishing runs, the job is `PUBLISHING`. If publishing fails after the slug was reserved (for example `PUBLISH_ASSET_ERROR`), the website becomes `PUBLISH_FAILED`, the job returns to `PREVIEW_READY`, and the failure is reported with the standard error body. Publishing has no automatic retry; it is idempotent for the same website and slug, so the frontend may repeat it.

### 3.5 POST /api/jobs/{jobId}/retry

**Purpose**

Lets the user retry a failed job once it has reached `FAILED`.

**Request:** no body.

**Valid when:** the job is `FAILED` and the stored failure has `retryable = true`. Otherwise the response is `409 Conflict` with code `JOB_NOT_RETRYABLE`.

**Processing Behavior**

1. Authenticate the user and verify job ownership.
2. Source failure (CV): reset only the failed tasks to `PENDING`, increment `job_tasks.attempt`, and re-publish the request events with the new `attempt`. The existing task rows are reused.
3. Website generation failure: move the job `FAILED → GENERATING`, ask the Website Service to reset the **same** website row `GENERATION_FAILED → GENERATING` with a fresh lease, and re-publish `profile.ready` for the same `profileId`. No second website is created.
4. Return the job status.

**Success Response — 202 Accepted:** the same body as `GET /api/jobs/{jobId}`.

Retrying a skipped optional source (a job in `PREVIEW_READY` with a warning) is not handled by this endpoint. In the MVP it would create a new job; this can be dropped from v1.

### 3.6 GET /api/websites

**Purpose**

Lists the signed-in user's websites for the "My sites" page: website identifier, status, slug and public URL when published.

## 4. Internal API — Core Backend ↔ Website Service

**Base path:** `/internal`

These endpoints are accessible only to authorized backend components.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/internal/websites/{websiteId}/preview` | Retrieve generated website draft |
| POST | `/internal/websites/{websiteId}/publish` | Publish approved website |
| POST | `/internal/websites/{websiteId}/retry-generation` | Reset a failed generation so it can be retried |

### 4.1 GET /internal/websites/{websiteId}/preview

**Producer / Caller:** Core Backend Service  
**Consumer:** Website Service

**Purpose**

Retrieves the generated website draft stored by the Website Generator.

**Request**

- Path parameter: `websiteId`
- Authenticated service-to-service identity
- Authorized user context, using the agreed internal authentication mechanism

**Response — 200 OK**

Returns `WebsitePreview` (Shared Data Contracts §9.3).

The Website Service reads the draft from PostgreSQL and returns the content needed for preview.

### 4.2 POST /internal/websites/{websiteId}/publish

**Producer / Caller:** Core Backend Service  
**Consumer:** Website Service

**Purpose**

Requests publication of an approved website using the selected subdomain.

**Request Body**

```json
{
  "slug": "alex-popescu"
}
```

**Processing Behavior**

1. Verify the authorized service request.
2. Retrieve the requested website draft.
3. Validate the requested slug.
4. Reject reserved or unavailable slugs.
5. Atomically reserve the slug in PostgreSQL.
6. Set the website to `PUBLISHING` and write `website.publish.requested` to the Website Service outbox (queue `website-publishing`).
7. Return `202 Accepted` with `{ websiteId, slug, status: "PUBLISHING" }`.

**Asynchronous continuation.** The Publisher consumes `website.publish.requested`, re-validates the draft, calls the render worker (Lambda container image), uploads the files to Amazon S3 (`index.html` last), updates publishing metadata and publishes `website.published`; on failure it publishes `website.failed` with `stage = WEBSITE_PUBLISHING`.

**Success Response — 202 Accepted**

Returns the website identifier, slug and status `PUBLISHING`. A repeat for the same website and slug returns `202` while publishing and `200` with the public URL once `PUBLISHED`.

**Conflict Response — 409 Conflict**

Returned when the selected slug is already in use.

A `202` means publication was accepted, not completed. Completion is reported through the `website.published` event and the job status.

### 4.3 POST /internal/websites/{websiteId}/retry-generation

**Producer / Caller:** Core Backend Service  
**Consumer:** Website Service

Resets a website in `GENERATION_FAILED` to `GENERATING` with a fresh generation lease before Core re-publishes `profile.ready`. The normal claim path then sees a `GENERATING` row. A stale duplicate `profile.ready` that arrives later for a `GENERATION_FAILED` row is simply deleted.

Returns `200 OK`. Returns `409 Conflict` when the website is not in `GENERATION_FAILED`.

## 5. Authentication and Authorization

### 5.1 Public API Authentication

Users authenticate using Google or GitHub OAuth.

The Core Backend Service is responsible for establishing and validating the authenticated user identity. The session is an httpOnly, host-only cookie (`pf_session`); the GitHub analysis uses one server-side token and no user OAuth token is stored.

All protected endpoints must verify the user's authorization before accessing application resources.

### 5.2 Internal Service Authentication

Requests between the Core Backend Service and Website Service must be authenticated independently from user-facing authentication.

Internal endpoints must not trust an arbitrary user identifier supplied by an unauthenticated caller.

The implementation must ensure that only the authorized Core Backend Service can invoke internal website operations.

### 5.3 Resource Ownership

Users can only access their own processing jobs and website drafts.

The Core Backend Service validates ownership before forwarding internal requests.

The Website Service remains responsible for enforcing website publishing constraints and global slug uniqueness.

## 6. HTTP Status Codes and Error Responses

All HTTP endpoints should use consistent status codes.

| HTTP Status | Meaning |
| --- | --- |
| 200 OK | Operation completed successfully |
| 202 Accepted | Asynchronous processing job accepted |
| 400 Bad Request | Malformed request |
| 401 Unauthorized | Missing or invalid authentication |
| 403 Forbidden | Insufficient permissions |
| 404 Not Found | Requested resource does not exist or is inaccessible |
| 409 Conflict | Slug conflict or invalid resource state |
| 413 Payload Too Large | Uploaded file exceeds the configured limit |
| 415 Unsupported Media Type | Unsupported uploaded document format |
| 422 Unprocessable Content | Invalid request field values |
| 429 Too Many Requests | Request, upload or generation limit reached (`RATE_LIMITED`) |
| 500 Internal Server Error | Unexpected server failure |
| 503 Service Unavailable | Required service temporarily unavailable |

**Standard Error Response**

```json
{
  "error": {
    "code": "SLUG_TAKEN",
    "message": "The requested subdomain is unavailable.",
    "requestId": "req-123"
  }
}
```

Error codes used by the API include `SLUG_TAKEN`, `SLUG_CONFLICT`, `PUBLISH_ASSET_ERROR`, `JOB_NOT_RETRYABLE` and `RATE_LIMITED`, plus the failure `errorCode` values in Shared Data Contracts §3.3.

Error responses must not expose internal credentials, private documents, stack traces, or sensitive user information.

## 7. Validation Rules

HTTP requests must be validated before business operations are performed.

**File Upload Validation**

- Verify supported document formats.
- Enforce configured file size limits.
- Reject invalid or malformed uploads.
- Store uploaded documents in private storage.

**GitHub Input Validation**

- Accept a valid GitHub username or normalized profile URL.
- Reject malformed or unsupported input.

**Website Slug Validation**

- Accept lowercase letters, numbers, and hyphens.
- Maximum length: 63 characters.
- Reject slugs starting or ending with a hyphen.
- Reject reserved infrastructure names such as `www`, `api`, `admin`, and `app`.
- Enforce global uniqueness through PostgreSQL.

**Authorization Validation**

- Verify authentication for all protected endpoints.
- Check resource ownership.
- Prevent unauthorized access to other users' jobs and websites.

## 8. Contract Ownership and Versioning

Each HTTP contract has one authoritative service owner.

| API Boundary | Contract Owner |
| --- | --- |
| Frontend → Core Backend | Core Backend Service |
| Core Backend → Website Service | Website Service |

The contract owner defines and maintains endpoint behavior, schemas, validation rules, and response semantics.

Consumers must implement integrations according to the agreed contracts.
