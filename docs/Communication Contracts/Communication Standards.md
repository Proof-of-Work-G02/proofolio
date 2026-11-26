# Communication Standards

**Project:** AI-Powered Personal Website Generator  
**Scope:** MVP / Cross-Service Communication  
**Technologies:** HTTP REST, Amazon SQS, Amazon S3, PostgreSQL

## 1. Purpose

This document defines the common communication standards and technical conventions that must be followed by all services within the application.

Its purpose is to ensure consistent, secure, and reliable communication across independently developed and deployed components.

The standards cover:

- API and event versioning.
- Message correlation and tracing.
- Idempotent processing.
- Error handling.
- Retry and timeout policies.
- Security and authorization.
- Data validation.
- Logging and observability.
- Contract testing and compatibility.
- Communication consistency across local and AWS environments.

These standards complement the HTTP API Contracts, SQS Event Contracts, and Shared Data Contracts.

---

## 2. General Communication Principles

All services must follow the same communication principles.

### 2.1 Explicit Service Boundaries

Each service has clearly defined responsibilities and communication interfaces.

A service must not depend on another service's internal implementation details.

Communication between independently deployable services takes place through the agreed mechanisms:

| Communication | Technology |
| --- | --- |
| Frontend ↔ Core Backend | HTTP REST |
| Core Backend → AI Processing Services | Amazon SQS |
| AI Processing Services → Core Backend | Amazon SQS + S3 |
| Core Backend → Website Generator | Amazon SQS |
| Core Backend ↔ Website Service | HTTP REST |
| Website Service → Core Backend | Amazon SQS |
| Website Service (API) → Website Publisher | Amazon SQS (`website-publishing`) |
| Website Publisher → Render worker | HTTPS (Lambda, HMAC-signed) |
| Data persistence | PostgreSQL / S3 |

Internal modules belonging to the same deployable service communicate through application-level calls and do not require separate HTTP or SQS interfaces.

### 2.2 Contract-First Development

Service interfaces must be agreed upon before dependent components are implemented independently.

Each producer is responsible for generating data that conforms to the agreed contract.

Each consumer is responsible for validating incoming data against the supported contract.

Changes affecting shared interfaces must be reviewed by both producers and consumers.

### 2.3 Independent Deployment

Each microservice must be independently buildable, testable, and deployable.

A service deployment should not require deploying every other service unless a coordinated breaking contract change makes it necessary.

Services must not directly import application code from another independently deployable service.

Shared data structures may be generated from centrally maintained contracts.

### 2.4 Technology Independence

The communication contracts must remain logically consistent across local development and AWS deployment.

Environment-specific configuration must not change the meaning or structure of exchanged data.

---

## 3. Naming and Formatting Conventions

### 3.1 JSON Naming

All shared JSON fields use **camelCase**.

Examples:

- `jobId`
- `taskId`
- `userId`
- `sourceType`
- `schemaVersion`
- `resultS3Key`
- `websiteId`

Backend implementations may use their language-specific internal naming conventions, but serialized contract fields must match the agreed JSON Schemas.

### 3.2 Event Naming

SQS event names use lowercase dot-separated identifiers.

The event names are:

- `cv.extract.requested`
- `github.analyze.requested`
- `linkedin.extract.requested`
- `processing.completed`
- `profile.ready`
- `website.generated`
- `website.publish.requested`
- `website.published`
- `processing.failed`
- `website.failed`

Event names must remain consistent across producers, consumers, documentation, and automated tests.

### 3.3 Identifier Conventions

Identifiers must be treated as opaque strings unless the corresponding contract defines a more restrictive format.

Examples include:

- `jobId`
- `taskId`
- `userId`
- `profileId`
- `websiteId`

Consumers must not infer business meaning from identifier prefixes or generate related identifiers by modifying existing strings.

The `eventId` format is UUID.

### 3.4 Date and Time Formatting

Event timestamps use UTC and RFC 3339-compatible date-time strings.

Example:

```json
{
  "occurredAt": "2026-11-17T14:30:00Z"
}
```

Professional information extracted from source documents may contain less precise dates:

- `YYYY`
- `YYYY-MM`
- `YYYY-MM-DD`

The precision of extracted dates must be preserved.

A date without a month or day must not be expanded using invented values.

---

## 4. Contract Versioning and Compatibility

### 4.1 Versioning Strategy

HTTP interfaces, SQS events, and shared JSON schemas are versioned to support independent service evolution.

The MVP contract version is **1**.

SQS events and stored shared data structures use:

```json
{
  "schemaVersion": 1
}
```

This identifies the major version of the corresponding contract.

HTTP API specifications are maintained using OpenAPI 3.1.

SQS interfaces are documented using AsyncAPI and JSON Schema.

### 4.2 Backward-Compatible Changes

Examples of backward-compatible changes include:

- Adding a new optional JSON field.
- Adding optional metadata without changing existing field meanings.
- Improving internal processing without changing its output schema.
- Adding a new independent API endpoint.

An optional field is backward-compatible only when existing consumers and schema validators permit the addition.

Consumers must not automatically accept unknown fields unless that behavior is explicitly allowed by the agreed schema.

### 4.3 Breaking Changes

Examples of breaking changes include:

- Removing an existing required field.
- Renaming a JSON field.
- Changing the type of a field.
- Changing the meaning of an existing value.
- Changing an HTTP endpoint's established behavior.
- Adding an enum value that existing consumers cannot handle.
- Replacing an existing event with an incompatible payload.

Breaking changes require a new contract version or an explicitly coordinated migration.

### 4.4 Compatibility Rules

Before merging a breaking contract change:

1. Identify the affected producers and consumers.
2. Review the proposed changes with the responsible teams.
3. Introduce the new contract version.
4. Update consumer implementations or provide a compatibility period.
5. Run contract and integration tests.
6. Deploy the coordinated changes.

Older contract versions must not be removed while active consumers still depend on them.

---

## 5. Idempotency Standards

### 5.1 Purpose

Idempotency ensures that processing the same logical operation multiple times does not create unintended duplicate effects.

This is particularly important because Amazon SQS Standard uses at-least-once delivery and does not guarantee strict ordering.

A message may be delivered more than once, even if the producer sends it only once.

All SQS consumers must implement idempotent processing.

### 5.2 Event-Level vs Business-Level Deduplication

Event metadata includes `eventId`, which uniquely identifies a particular event emission.

However, `eventId` must not be the only mechanism used to prevent duplicate business operations.

The same logical task may be represented by multiple event emissions during retries or recovery.

Consumers must also identify operations using stable business identifiers.

### 5.3 Idempotency Keys

| Operation | Logical Idempotency Key |
| --- | --- |
| CV extraction | taskId |
| GitHub analysis | taskId |
| LinkedIn extraction | taskId |
| Processing completion | taskId |
| Processing failure | taskId |
| Website failure | profileId |
| Profile aggregation | jobId |
| Website generation | profileId (`UNIQUE(websites.profile_id)`) |
| Website publication | websiteId + slug (compare-and-set on website status) |

### 5.4 Processing Rules

Consumers must verify whether a logical operation has already completed before applying additional business state changes.

Examples:

**CV Extraction**

Receiving `cv.extract.requested` twice must not create two authoritative results for the same completed task.

**Processing Completion**

Receiving `processing.completed` twice must not insert duplicate authoritative extraction results or trigger profile aggregation twice.

**Profile Aggregation**

A processing job must not generate multiple unified profiles because duplicate completion events were received.

**Website Generation**

Repeated `profile.ready` messages must not create multiple websites for the same logical generation operation.

**Website Publication**

Repeated publication requests for the same website and slug must not create duplicate publications, and a repeated `website.publish.requested` must not publish twice.

A repeated successful publication request returns the existing published URL.

### 5.5 Concurrency Considerations

Checking whether an operation already exists is not sufficient when multiple workers can execute concurrently.

Where applicable, idempotency is enforced through atomic database operations, uniqueness constraints, or equivalent concurrency-safe mechanisms.

The system must not rely exclusively on in-memory deduplication.

---

## 6. HTTP Communication Standards

### 6.1 General Requirements

HTTP APIs follow consistent REST conventions.

**General Rules**

- Use HTTPS for deployed communication.
- Use JSON for structured request and response bodies.
- Use `multipart/form-data` for the initial portfolio source upload.
- Use appropriate HTTP methods and status codes.
- Validate requests before performing business operations.
- Return structured error responses.
- Authenticate protected endpoints.
- Enforce resource ownership.

### 6.2 HTTP Methods

| Method | Usage |
| --- | --- |
| GET | Retrieve resources without modifying their state |
| POST | Create jobs or initiate business operations |
| DELETE | Remove the caller's own account and data (`DELETE /api/me`) |

The MVP does not use PUT or PATCH.

### 6.3 HTTP Status Codes

The application uses the status codes defined in HTTP API Contracts.

Important distinctions:

- `200 OK` — The requested synchronous operation completed successfully.
- `202 Accepted` — The request was accepted for asynchronous processing (for example, publishing).
- `400 Bad Request` — The request is malformed.
- `401 Unauthorized` — Authentication is missing or invalid.
- `403 Forbidden` — The caller lacks permission.
- `404 Not Found` — The requested resource does not exist or is not accessible.
- `409 Conflict` — The request conflicts with existing state (for example, `SLUG_TAKEN`, `SLUG_CONFLICT`).
- `422 Unprocessable Content` — The request contains invalid values.
- `429 Too Many Requests` — A rate limit was hit (`RATE_LIMITED`).
- `500 Internal Server Error` — An unexpected failure occurred.
- `503 Service Unavailable` — A required service is unavailable.

The exact response definitions belong to HTTP API Contracts.

### 6.4 Standard Error Response

HTTP errors use a consistent JSON structure.

```json
{
  "error": {
    "code": "SLUG_TAKEN",
    "message": "The requested subdomain is unavailable.",
    "requestId": "req-123"
  }
}
```

**Field Definitions**

| Field | Description |
| --- | --- |
| code | Stable machine-readable application error |
| message | Human-readable error description |
| requestId | Identifier used to trace the request |

Clients should use stable error codes rather than parsing human-readable messages to determine application behavior.

Error messages must not reveal internal implementation details or sensitive information.

### 6.5 HTTP Retry Safety

Clients must distinguish between operations that can be safely repeated and operations that may produce additional side effects.

**GET Requests**

GET requests are read-only and may be retried for transient infrastructure failures, subject to the configured retry policy.

**POST /api/jobs**

Creating a job is not automatically idempotent.

If the client retries after losing the response, the server may have already created the original job. The client should not retry a job creation automatically; it checks the job list first.

**POST /api/jobs/{jobId}/retry**

Retrying a failed job reuses the same job and website. Only retryable failures can be retried; otherwise the call returns `JOB_NOT_RETRYABLE`.

**POST /api/websites/{websiteId}/publish**

Publishing is asynchronous and idempotent for the same website and slug. The first request returns `202 Accepted` with status `PUBLISHING`. A repeated request while publishing returns `202`; after successful publication it returns `200` with the existing publication result.

Publishing a previously published website under a different slug is a conflict (`409 SLUG_CONFLICT`); slugs cannot be renamed in v1.

### 6.6 Internal HTTP Communication

Internal Website Service endpoints must only be accessible to authorized backend components.

The Core Backend Service validates user ownership before forwarding requests.

The Website Service independently validates the authenticated service identity and enforces applicable website ownership and publishing constraints.

The authenticated actor's identity is forwarded using `X-Actor-User-Id`.

This header is contextual information, not an authentication mechanism. It is trusted only when supplied by an authenticated, authorized internal caller.

Service-to-service calls, including calls to the render worker, are authenticated with HMAC-signed requests.

---

## 7. SQS Communication Standards

### 7.1 Message Format

SQS messages use UTF-8 encoded JSON.

The message body must conform to the corresponding event schema.

All v1 event payloads contain common metadata such as:

- `schemaVersion`
- `eventId`
- `event`
- `occurredAt`
- `jobId`

Event-specific identifiers and fields are defined in SQS Event Contracts.

### 7.2 Delivery Semantics

Amazon SQS Standard provides at-least-once delivery without strict ordering guarantees.

Therefore:

- Consumers must support duplicate delivery.
- Consumers must not rely on message arrival order.
- Business state changes must be idempotent.
- Processing progress must be persisted.
- Acknowledgement must follow successful handling.

### 7.3 Message Acknowledgement

A consumer acknowledges or deletes an SQS message only after the required processing is durably completed.

For example, a CV extraction worker:

1. Receives the request.
2. Validates the message.
3. Retrieves the input document.
4. Extracts structured data.
5. Validates the output.
6. Stores the result in S3.
7. Publishes the completion event.
8. Deletes the original request message.

If processing fails before the operation is durably completed, the message is not acknowledged as successfully processed.

### 7.4 Message Ordering

Processing tasks run independently and may finish in any order.

For example, GitHub analysis may finish before CV extraction.

The Core Backend determines aggregation readiness using persisted task states rather than the order in which completion events arrive.

State transitions must not incorrectly move a completed job or task back into an earlier state.

### 7.5 Message Validation

Each consumer must validate:

- Event type.
- Supported schema version.
- Required identifiers.
- Field types.
- Valid enum values.
- Required storage references.
- Event-specific required fields.

The Core Backend additionally verifies that `taskId`, `jobId`, and `sourceType` match its authoritative PostgreSQL records.

A valid JSON message does not automatically imply that the referenced business operation is authorized or legitimate.

### 7.6 Large Payload Handling

SQS messages must not contain:

- Uploaded CV documents.
- LinkedIn PDF documents.
- Complete repository documentation.
- Complete extraction results.
- Unified professional profiles.
- Generated website drafts.
- Credentials or access tokens.

Large data is stored in Amazon S3 or PostgreSQL.

Messages carry identifiers and references to that data.

---

## 8. Retry and Timeout Policies

### 8.1 General Principles

Distributed operations may fail temporarily due to network interruptions, unavailable dependencies, rate limits, or infrastructure errors.

Services must distinguish between transient failures and permanent failures.

Starting values for retry counts, delays and timeouts are set in the Failure Handling Design and are tuned after measuring real runtimes.

### 8.2 Transient Failures

Transient failures include:

- Temporary network connectivity failures.
- Service unavailability.
- Database connection interruptions.
- Temporary S3 or SQS API errors.
- External AI provider rate limiting.
- GitHub API rate limiting.

These failures are retried according to the integration's retry policy.

### 8.3 Permanent Failures

Permanent failures include:

- Invalid message schemas.
- Unsupported document formats.
- Invalid input references.
- Unsupported contract versions.
- Unauthorized access.
- Requests that violate business validation rules.

These failures are not retried indefinitely.

### 8.4 Retry Strategy

The retry strategy uses:

- Bounded retry attempts.
- Exponential backoff.
- Jitter to reduce synchronized retry traffic.
- Respect for external provider retry guidance.
- Idempotent operations.
- Structured logging of retry attempts.

Retries must not create duplicate business operations.

### 8.5 HTTP Timeouts

Each outbound HTTP integration defines:

- Connection timeout.
- Response/read timeout.
- Maximum retry attempts.
- Overall request deadline where applicable.

Timeouts reflect the expected behavior of each dependency. The GitHub API, AI providers, the render worker and the internal Website Service use different timeout configurations.

### 8.6 SQS Visibility Timeout

SQS consumers use visibility timeout settings appropriate for their processing duration.

Long-running AI processing operations extend message visibility while processing remains active.

A message that is not successfully completed and deleted before its visibility timeout expires becomes available for another processing attempt.

This does not eliminate the need for idempotency.

### 8.7 Dead-Letter Queues

Each source queue has a DLQ (`cv-extraction-dlq`, `github-analysis-dlq`, `linkedin-extraction-dlq`, `website-generation-dlq`, `website-publishing-dlq`, `processing-results-dlq`). Visibility timeouts, `maxReceiveCount` and retention are in SQS Event Contracts §2.1.1.

- **Transient failures** are retried in-process, then by SQS redelivery.
- **Permanent business failures** publish a failure event and delete the request message immediately.
- **Poison messages** (malformed, unsupported `schemaVersion`, missing field, unknown `jobId`) are not processed and no failure event is sent. They are left to reach the DLQ.
- A DLQ listener in the Core Backend marks the affected job, task or website as failed with `RETRIES_EXHAUSTED`. DLQ messages are never deleted automatically; an operator inspects and redrives them manually.
- Two failure events exist: `processing.failed` and `website.failed` (SQS Event Contracts §5.2 and §6.5). A Core watchdog fails jobs stuck in a non-terminal state (`TIMEOUT`).
- Optional sources: a failed GitHub or LinkedIn task does not fail the job. Core records a warning and continues from the CV. A failed CV fails the job.

### 8.8 Abuse Limits

The public API applies rate limits to requests, uploads and job creation. A request over the limit returns `429` with `RATE_LIMITED` and a `Retry-After` header.

---

## 9. Data Consistency and State Management

### 9.1 Data Ownership

Services must respect the data ownership boundaries defined by the architecture.

| Data | Owner |
| --- | --- |
| Users, OAuth accounts and sessions | Core Backend |
| Processing jobs and tasks | Core Backend |
| Extraction result records | Core Backend |
| Unified profiles | Core Backend |
| Generated website drafts | Website Service |
| Website publishing metadata | Website Service |
| Original uploaded documents | Core Backend |
| Structured extraction files | Producing AI Services |
| Published static website files | Website Service |

AI Processing Services must not directly modify Core Backend PostgreSQL tables.

The Website Service may read Core-owned unified profiles according to the established architecture but must not modify them.

The Core Backend accesses Website Service functionality through its agreed communication interfaces.

### 9.2 Consistency Across PostgreSQL, S3, and SQS

The application uses multiple storage and communication systems.

A single atomic transaction cannot directly cover PostgreSQL, Amazon S3, Amazon SQS, and external HTTP services.

Therefore, operations are designed to tolerate partial completion and retries.

**Processing Result Example**

1. The AI service generates a valid result.
2. The result is stored in S3.
3. The service publishes `processing.completed`.
4. Core Backend records the result and marks the task completed.

If the completion event fails to publish after the S3 write, the request message is not deleted, so it is redelivered and the work is retried without producing inconsistent results.

### 9.3 Reliable Event Publication

The Core Backend and the Website Service each use a transactional outbox for the events they publish after a database change: the state change and an `outbox` row are written in one transaction, and a relay publishes and marks rows sent. Services without their own database publish first and delete the request message afterwards.

A relay crash can publish an event twice, which consumers tolerate.

### 9.4 Website Publishing Consistency

Website publishing requires coordination between PostgreSQL, SQS, the render worker and S3.

The publish request (synchronous part) does the following in one transaction:

1. Validates the publication request.
2. Moves the website to `PUBLISHING` with a compare-and-set.
3. Atomically reserves the selected slug.
4. Writes the `website.publish.requested` outbox row.

The HTTP call then returns `202 Accepted`.

The Website Publisher consumes `website.publish.requested` from the `website-publishing` queue and:

1. Calls the render worker (Node, Lambda container image, HMAC-authenticated) to render the static files.
2. Uploads the static files to S3, with `index.html` last.
3. Persists the publication result.
4. Publishes `website.published`.

On failure it publishes `website.failed` (`stage = WEBSITE_PUBLISHING`); the website becomes `PUBLISH_FAILED` and Core returns the job to `PREVIEW_READY`. The user keeps the draft and may publish again.

A publication is not reported as successfully completed when required assets or metadata are missing. Re-uploading the same files to the same slug is safe, so a retried publish is idempotent.

### 9.5 State Transitions

Job and task state transitions are controlled by the owning service.

Late or duplicate messages must not overwrite newer durable states.

The authoritative job status is maintained by Core Backend.

A transition is applied with a compare-and-set, for example `UPDATE jobs SET status = :new WHERE id = :id AND status = ANY(:allowed_from)`. If zero rows change, the event is a duplicate or stale one and is acknowledged without side effects.

Website generation and publication states are maintained by the Website Service and synchronized with Core Backend through the agreed interfaces. The frontend learns about both by polling the job status.

---

## 10. Correlation and Distributed Tracing

### 10.1 Purpose

Distributed operations span multiple services, queues, and storage systems.

Correlation identifiers allow developers to trace a processing operation across those components.

### 10.2 Correlation Identifiers

| Identifier | Purpose |
| --- | --- |
| requestId | Trace an HTTP request |
| eventId | Identify a specific event emission |
| jobId | Trace the overall portfolio generation workflow |
| taskId | Trace an individual AI processing task |
| profileId | Identify the generated unified profile |
| websiteId | Identify the generated website |

Not every identifier is required in every message.

The exact required fields are defined by the individual contracts.

### 10.3 Correlation Example

A single job may generate the following records:

```
jobId: job-456
  |
  |-- taskId: task-789 (CV)
  |-- taskId: task-790 (GitHub)
  |-- taskId: task-791 (LinkedIn)
  |
  |-- profileId: profile-456
  |
  |-- websiteId: website-456
```

All relevant logs include available correlation identifiers.

### 10.4 HTTP Request Tracing

HTTP requests are associated with a request identifier carried in the `X-Request-Id` header.

The Core Backend generates or validates a request identifier when processing incoming requests.

Internal HTTP calls propagate this identifier.

A request identifier is used for diagnostics and must not be treated as authentication or business ownership information.

### 10.5 Structured Logging

Services produce structured logs using a consistent format.

**Log Example**

```json
{
  "timestamp": "2026-11-17T14:31:00Z",
  "level": "INFO",
  "service": "cv-extraction",
  "event": "processing.completed",
  "jobId": "job-456",
  "taskId": "task-789",
  "message": "CV extraction completed successfully"
}
```

Logs contain relevant diagnostic metadata without exposing complete source documents or extracted personal information.

---

## 11. Security Standards

### 11.1 Authentication

The Frontend authenticates users through the authentication functionality exposed by Core Backend.

The application supports Google and GitHub OAuth, implemented in the Core Backend. After login Core creates a server-side session and sets an httpOnly, host-only cookie named `pf_session`. OAuth tokens are not stored.

Protected public APIs validate the session and the authenticated user.

### 11.2 Authorization

Core Backend verifies ownership before allowing users to access:

- Processing jobs.
- Generated website drafts.
- Website publishing operations.
- The "my sites" list.

Internal service-to-service requests require authenticated service identities.

A caller-provided user identifier must not be accepted as proof of authorization.

### 11.3 Least-Privilege Access

Services receive only the permissions required to perform their responsibilities.

Examples:

- Core Backend can write uploaded documents.
- CV Extractor can read the required CV documents.
- LinkedIn Extractor can read the required LinkedIn documents.
- AI Processing Services can write their extraction results.
- Core Backend can read extraction results.
- Website Service can read unified profiles.
- Website Service can write published website assets.
- The render worker can be invoked only by the Website Publisher and has no database access.

Access restrictions are enforced through service credentials, database privileges, and storage permissions.

### 11.4 Sensitive Data

The system processes personal and professional information.

Services must avoid exposing:

- CV contents in logs.
- LinkedIn profile documents in messages.
- OAuth access tokens.
- API keys.
- S3 credentials.
- Database credentials.
- Sensitive data belonging to other users.

Configuration secrets are not committed to Git repositories.

A user can delete their account and all their data with `DELETE /api/me`.

### 11.5 Untrusted Inputs

Uploaded documents, GitHub repository content, and AI-generated output are treated as untrusted input.

External source content must not be interpreted as application-level instructions.

AI-generated website content is validated before rendering or publication.

Generated content must not be allowed to execute unrestricted code or access confidential application resources.

### 11.6 Public Website Isolation

Published websites share common S3 and CloudFront infrastructure.

Routing and storage access must prevent one website from accessing another website's files through path manipulation or malicious input.

Subdomain uniqueness is enforced through PostgreSQL constraints. Because the session cookie is host-only, a published site on a subdomain never receives it.

---

## 12. Contract Validation and Testing

### 12.1 Contract Validation

Every producer validates its output against the agreed contract before publishing or returning it.

Every consumer validates incoming data before relying on it.

**Required Validation Boundaries**

| Boundary | Validation |
| --- | --- |
| Frontend → Core Backend | HTTP request validation |
| Core Backend → AI Service | SQS event schema |
| AI Service → S3 | Extraction result schema |
| AI Service → Core Backend | Completion event schema |
| S3 → Core Backend | Extraction result validation |
| Core Backend → Website Service | Profile and event schemas |
| Website Service → Core Backend | HTTP and event schemas |
| Website Service → Frontend | Website draft schema |
| Website Publisher → Render worker | Render request and response schema |

### 12.2 Machine-Readable Contracts

The shared GitHub repository contains machine-readable specifications.

```
contracts/
  openapi/
    core-api.yaml
    website-internal-api.yaml

  asyncapi/
    events.yaml

  schemas/
    common/
    extraction/
    profile/
    website/

  examples/
    http/
    events/
    data/
```

The precise file organization may differ, but the contracts remain centrally versioned and accessible to every team.

### 12.3 Unit Tests

Each service tests its own validation and processing logic independently.

Examples:

- Invalid document metadata.
- Missing required event fields.
- Unsupported schema versions.
- Invalid S3 references.
- Invalid website slugs.
- Duplicate processing requests.

### 12.4 Contract Tests

Contract tests verify that producers and consumers agree on the structure and meaning of exchanged data.

Examples:

- Core Backend generates a valid `cv.extract.requested` message.
- CV Extraction Service accepts the agreed request payload.
- CV Extraction Service generates a valid `CVExtractionResult`.
- Core Backend successfully validates the extraction result.
- Website Service accepts the agreed `profile.ready` event.
- Website Publisher accepts the agreed `website.publish.requested` event.
- Frontend can render the agreed `WebsiteDraft`.

Contract tests run automatically in CI when relevant interfaces or services change.

### 12.5 Integration Tests

Integration tests verify communication between components using real protocol interactions.

The local environment uses:

- Docker Compose.
- PostgreSQL.
- ElasticMQ.
- RustFS.
- Service containers.

Integration testing verifies:

- SQS message publication and consumption.
- S3 object storage and retrieval.
- HTTP request/response behavior.
- Database state updates.
- Event correlation.
- Idempotent handling of duplicates.

### 12.6 End-to-End Tests

The MVP supports an end-to-end Happy Flow test covering:

1. User submits portfolio sources.
2. Core Backend creates processing tasks.
3. AI Processing Services generate extraction results.
4. Core Backend aggregates the results.
5. Website Service generates the draft.
6. Frontend retrieves the preview.
7. User approves publication and receives `202`.
8. The Website Publisher publishes the website.
9. The frontend sees `PUBLISHED` by polling, and the public website becomes accessible.

### 12.7 Failure and Reliability Tests

Before production deployment, integration tests additionally cover:

- Duplicate SQS messages.
- Out-of-order completion messages.
- Temporary unavailable dependencies.
- Invalid messages.
- Timeout and retry behavior.
- Failed event publication.
- Partial S3/Database operations.
- Concurrent requests for the same website slug.
- A failed publish returning the job to `PREVIEW_READY`.

---

## 13. Logging, Monitoring, and Observability

### 13.1 Logging Requirements

Every service produces structured logs containing:

- Timestamp.
- Log level.
- Service name.
- Operation or event type.
- Available correlation identifiers.
- Processing outcome.
- Sanitized error information when relevant.

Sensitive document contents and credentials must not be included in logs.

### 13.2 Monitoring

The application monitors:

- Processing job completion.
- Task execution duration.
- Failed processing attempts.
- SQS queue backlog and DLQ depth.
- Repeated message deliveries.
- HTTP request failures.
- AI provider failures.
- Website generation and publication outcomes.

### 13.3 Local and AWS Monitoring

Local development uses application and container logs.

AWS deployment uses Amazon CloudWatch for centralized logging and infrastructure monitoring.

---

## 14. Local and AWS Communication Consistency

The project follows a local-first development strategy.

Both environments preserve the same logical service boundaries and contracts.

| Component | Local | AWS |
| --- | --- | --- |
| HTTP services | Docker Compose | Selected AWS compute |
| Render worker | Container run locally | AWS Lambda (container image) |
| Message queues | ElasticMQ | Amazon SQS Standard |
| Object storage | RustFS | Amazon S3 |
| Database | PostgreSQL Docker | Amazon RDS PostgreSQL |
| Published websites | Local routing simulation | S3 + CloudFront |

### 14.1 Environment Configuration

The following are configured externally:

- Database connection information.
- SQS endpoint and queue URLs.
- S3 endpoint and bucket names.
- Internal service base URLs and the render worker URL.
- External API credentials.
- Authentication configuration.
- Retry and timeout settings.

Environment-specific configuration must not be hardcoded in business logic.

### 14.2 Compatibility

Local and AWS environments use the same:

- Event names.
- Event payload structures.
- JSON field naming.
- Shared data schemas.
- HTTP endpoint semantics.
- Data ownership rules.
- Logical workflow.

Local SQS and S3 compatibility does not eliminate the need for AWS integration testing.

Production behavior is verified against actual AWS infrastructure before deployment is considered complete.

---

## 15. Contract Ownership and Change Management

### 15.1 Ownership

Each contract has an identified owner responsible for maintaining it.

| Contract Category | Responsible Service |
| --- | --- |
| Public HTTP APIs | Core Backend |
| Internal Website HTTP APIs | Website Service |
| Processing request events | Core Backend |
| Processing completion event | Shared / Core Backend coordinates |
| Website lifecycle events (including `website.publish.requested`) | Website Service |
| CV result schema | CV Extraction Service |
| GitHub result schema | GitHub Analysis Service |
| LinkedIn result schema | LinkedIn Extraction Service |
| Unified profile schema | Core Backend |
| Website draft schema | Website Service |

### 15.2 Change Review

Changes to shared contracts are reviewed by the affected producer and consumer teams.

The workflow is:

1. Create a pull request modifying the shared contract.
2. Document the compatibility impact.
3. Request review from affected service owners.
4. Run schema validation and contract tests.
5. Merge after approval.
6. Update service implementations according to the agreed compatibility strategy.

### 15.3 Documentation Responsibilities

The GitHub `contracts/` directory contains the authoritative machine-readable specifications.

Confluence documents the communication architecture, business meaning, responsibilities, and architectural decisions.

When contracts change, documentation is updated to remain consistent with the version-controlled definitions.

---

## 16. Out of Scope for v1

- Worker concurrency limits, metrics and alert thresholds, distributed tracing and log retention are set with the infrastructure.
- Durable idempotency records beyond database uniqueness, and reprocessing beyond manual DLQ redrive.
- Profile editing, preview editing, photo upload and third-party templates.
