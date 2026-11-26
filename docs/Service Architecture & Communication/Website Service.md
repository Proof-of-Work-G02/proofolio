# Website Service

**Service Type:** Backend Microservice  
**Main Responsibility:** AI-powered website generation, preview and publishing

**Scope:** Happy Flow only

---

## 1. Purpose

The Website Service is responsible for transforming a user's unified profile into a personalized portfolio website based on a selected template.

The service integrates with an external AI provider to generate website content, allows the user to preview the generated website, and publishes the approved website to Amazon S3.

Published websites are delivered through Amazon CloudFront and made available through unique user subdomains.

**Example:** `https://username.ourdomain.com`

Each user can select a custom subdomain when publishing their website.

Subdomains must be globally unique across the platform. Two users can have the same name, but they cannot publish websites using the same subdomain.

The service contains two internal modules:

- **Website Generator**
- **Website Publisher**

---

## 2. Internal Modules

### 2.1 Website Generator Module

Responsible for generating personalized website drafts.

**Responsibilities:**

- Consume `profile.ready` events from Amazon SQS.
- Retrieve the user's unified profile from PostgreSQL.
- Retrieve the selected website template.
- Call an external AI provider to generate and adapt website content.
- Produce a website draft compatible with the selected template.
- Store the generated draft in PostgreSQL.
- Make the draft available for frontend preview.
- Publish a `website.generated` event.

**Inputs:**

- `jobId`
- `userId`
- `profileId`
- `templateId`

**Outputs:**

- Generated website draft
- `websiteId`
- Generation status

### 2.2 Website Publisher Module

Responsible for publishing approved websites under unique user subdomains.

**Responsibilities:**

- Receive publishing requests from the Core Backend Service. The HTTP call returns `202`; the work is driven by the `website.publish.requested` event on the `website-publishing` queue.
- Retrieve the approved website draft from PostgreSQL.
- Receive the user's selected subdomain slug.
- Validate the slug format and verify its availability.
- Reserve the unique slug using a PostgreSQL uniqueness constraint.
- Reject publication when the requested slug is already taken or reserved.
- Validate and prepare the generated website for deployment.
- Call the render worker (a Node service packaged as an AWS Lambda container image) to produce static HTML, CSS and assets.
- Upload static website files to the corresponding Amazon S3 location, with `index.html` last.
- Update website metadata, publishing status and public URL in PostgreSQL.
- Publish a `website.published` event, or `website.failed` with `stage = WEBSITE_PUBLISHING` on failure.

**Inputs:**

- `websiteId`
- `userId`
- Selected website slug

**Outputs:**

- Published website URL
- Publishing status

**Subdomain Rules:**

- Each published website must have a globally unique slug.
- Slugs contain lowercase letters, numbers and hyphens.
- Slugs cannot start or end with a hyphen.
- Slugs must be valid DNS hostname labels, with a maximum length of 63 characters.
- Reserved subdomains such as `www`, `api`, `admin` and `app` cannot be selected.
- Subdomain uniqueness is enforced at the database level.
- The slug is selected and reserved during website publishing, not during user registration.
- A user who already owns a slug through an older website may publish a newer website to it (slug takeover); the older website becomes `UNPUBLISHED`. Renaming a published slug is not supported in version 1.

**Example:**

Two users named Alex Popescu may select different subdomains:

- `alex-popescu.ourdomain.com`
- `alex-popescu-dev.ourdomain.com`

The user-facing application may suggest an alternative slug if the preferred one is unavailable.

---

## 3. Incoming Communication

The Website Service receives asynchronous processing messages through Amazon SQS and HTTP requests from the Core Backend Service.

| Source | Technology | Purpose |
| --- | --- | --- |
| Profile Aggregation Module | Amazon SQS (`website-generation`) | Receive `profile.ready` to start website generation |
| Core Backend Service | HTTP REST | Retrieve generated website for preview |
| Core Backend Service | HTTP REST | Request publication of the approved website using the selected subdomain (returns `202`) |
| Core Backend Service (via the Website Service outbox) | Amazon SQS (`website-publishing`) | Receive `website.publish.requested` to run the publication |

**Communication Flow:**

1. The Profile Aggregation Module publishes a `profile.ready` event.
2. The Website Generator consumes the event and generates the website.
3. The Core Backend Service retrieves the generated draft for frontend preview.
4. The user reviews the generated website.
5. The user selects a preferred subdomain and chooses Publish.
6. The Core Backend Service validates the user's authorization and forwards the publishing request to the Website Publisher.
7. The Website Publisher validates and reserves the unique subdomain, sets the website to `PUBLISHING`, queues `website.publish.requested` and returns `202`.
8. The Publisher consumes the event, renders and uploads the site, and publishes `website.published` (or `website.failed`).

The frontend communicates exclusively through the Core Backend API rather than accessing internal Website Service endpoints directly.

---

## 4. Outgoing Communication

| Destination | Protocol / Technology | Purpose |
| --- | --- | --- |
| PostgreSQL | SQL | Read unified profiles and store website drafts, metadata, unique slugs and publishing status |
| External AI Provider | HTTPS REST API | Generate personalized website content |
| Amazon S3 | AWS SDK / S3 API | Upload published static website files and assets |
| Amazon SQS (`processing-results`) | AWS SDK / SQS API | Send `website.generated`, `website.published` and `website.failed` events to Core Backend Service |
| Amazon SQS (`website-publishing`) | AWS SDK / SQS API | Receive `website.publish.requested` events from Core Backend Service (own DLQ) |
| Render worker (Lambda) | HTTP locally, Lambda invoke on AWS | Turn the approved draft into static files |

### Website Hosting & Subdomain Routing

Each published portfolio website is accessible through a unique user subdomain.

**Example:** `https://stefan-dobrincu.ourdomain.com`

The hosting infrastructure uses:

- **Amazon S3** to store published HTML, CSS, JavaScript and other assets.
- **Amazon CloudFront** to deliver published websites.
- **Wildcard DNS** to direct user subdomains to CloudFront.
- **Wildcard SSL/TLS Certificate** to provide HTTPS.
- **CloudFront Function** to route requests to the correct website files.

**Infrastructure Configuration:**

A wildcard DNS record:

`*.ourdomain.com`

directs user subdomains to the shared CloudFront distribution.

A wildcard SSL/TLS certificate covers the user subdomains.

The CloudFront distribution uses a CloudFront Function to identify the requested hostname and rewrite the URI to the corresponding S3 object.

The S3 origin remains private and is accessible to CloudFront through an appropriate origin access configuration.

**Routing Example:**

Incoming request:

```
Host: stefan-dobrincu.ourdomain.com
Path: /
```

CloudFront Function rewrites the request:

```
/stefan-dobrincu/index.html
```

For static assets:

```
Request:
https://stefan-dobrincu.ourdomain.com/assets/style.css

S3 Object:
/stefan-dobrincu/assets/style.css
```

The routing function must validate the requested hostname and enforce the correct website prefix so that requests cannot bypass subdomain isolation.

**Important Considerations:**

- All published websites share the same S3 bucket.
- All user subdomains share the same CloudFront distribution.
- A separate CloudFront distribution is not required for each user.
- A separate S3 bucket is not required for each user.
- Website visitors access the published static files without invoking the Website Service.
- The AI provider is called during website generation, not when visitors access an already published website.

---

## 5. Data Ownership

The Website Service owns website-related data in PostgreSQL and published website files in Amazon S3.

### 5.1 PostgreSQL

**Table:** `websites`

Stores website configuration, generated draft, subdomain information and publishing metadata.

| Field | Description |
| --- | --- |
| `id` | Unique website identifier |
| `user_id` | Website owner |
| `profile_id` | Associated unified profile |
| `template_id` | Selected website template |
| `slug` | Globally unique subdomain identifier |
| `status` | `GENERATING`, `GENERATION_FAILED`, `PREVIEW_READY`, `PUBLISHING`, `PUBLISH_FAILED`, `PUBLISHED`, `UNPUBLISHED` |
| `draft_content` | Generated website `content` (JSONB), the `content` part of the `WebsiteDraft` schema (Shared Data Contracts §9) |
| `s3_path` | Location of published static files |
| `published_url` | Public website URL |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |
| `generation_lease_expires_at` | Lease for the worker that owns generation |
| `error_code` | Last failure code |
| `error_message` | User-safe failure message |

The table columns (`id`, `profile_id`, `template_id`, `status`) are the single source of truth. `draft_content` does not repeat them and stores only the draft `content`. The preview API response adds them from the columns.

**Slug Constraints:**

The `slug` field must have a PostgreSQL `UNIQUE` constraint.

The slug can remain unset while the website is in the preview stage. It is assigned when the user publishes the website.

The uniqueness constraint is the authoritative mechanism for preventing conflicts between simultaneous publishing requests.

Checking slug availability before publishing is not sufficient on its own, because two requests may attempt to reserve the same slug concurrently.

The publishing operation must atomically reserve the slug in PostgreSQL before uploading the corresponding website files.

If the slug is already taken or reserved, the publishing request is rejected with a conflict response.

**Example:**

| user\_id | slug | published\_url |
| --- | --- | --- |
| user-123 | stefan-dobrincu | <https://stefan-dobrincu.ourdomain.com> |
| user-456 | stefan-dev | <https://stefan-dev.ourdomain.com> |
| user-789 | maria-popescu | <https://maria-popescu.ourdomain.com> |

The Website Service reads unified profiles from PostgreSQL but does not modify profile data owned by the Core Backend Service.

### 5.2 Amazon S3

Stores the published static website files.

All published websites are stored in the same S3 bucket, using separate prefixes based on their unique slugs.

**Example Structure:**

```
published-websites/
  stefan-dobrincu/
    index.html
    assets/
      style.css
      script.js
      profile.webp

  maria-popescu/
    index.html
    assets/
      style.css
      script.js
      profile.webp
```

In this example, `published-websites` represents the S3 bucket, while each user slug represents an object prefix within that bucket.

**Published URLs:**

```
https://stefan-dobrincu.ourdomain.com

https://maria-popescu.ourdomain.com
```

CloudFront uses hostname-based routing and URI rewriting to map each subdomain to its corresponding static files.

---

## 6. Events & API Endpoints

The following interfaces describe the communication required for the Happy Flow. Exact schemas are in SQS Event Contracts and Shared Data Contracts.

### 6.1 Consumed Events

**Event:** `profile.ready`

**Producer:** Core Backend Service / Profile Aggregation Module  
**Consumer:** Website Generator Module  
**Technology:** Amazon SQS Standard  
**Queue:** `website-generation`

This event indicates that the unified profile has been created and is ready for website generation.

The Website Generator retrieves the profile from PostgreSQL using the identifier included in the message.

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

The message carries identifiers only, never the full profile. Repeated delivery must not create a second website for the same generation operation.

**Event:** `website.publish.requested`

**Producer:** Website Publisher Module (HTTP handler, through the Website Service outbox)  
**Consumer:** Website Publisher Module  
**Technology:** Amazon SQS Standard  
**Queue:** `website-publishing` (with `website-publishing-dlq`)

Triggered when a publication has been accepted and the slug reserved. The message carries `websiteId`, `jobId`, `userId` and `slug` only. The consumer re-validates the draft, renders and uploads the site, then publishes `website.published` or `website.failed`.

### 6.2 Published Events

**Event:** `website.generated`

**Producer:** Website Generator Module  
**Consumer:** Core Backend Service / Job Orchestrator  
**Technology:** Amazon SQS Standard  
**Queue:** `processing-results`

Published after successful website draft generation.

The Core Backend Service processes the event and makes the generated website available for frontend preview.

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

**Event:** `website.published`

**Producer:** Website Publisher Module  
**Consumer:** Core Backend Service  
**Technology:** Amazon SQS Standard  
**Queue:** `processing-results`

Published after successful website publication.

**Example Payload:**

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440007",
  "event": "website.published",
  "occurredAt": "2026-11-17T14:35:00Z",
  "jobId": "job-456",
  "userId": "user-123",
  "websiteId": "website-456",
  "slug": "stefan-dobrincu",
  "status": "PUBLISHED",
  "url": "https://stefan-dobrincu.ourdomain.com"
}
```

The Core Backend Service uses this information to set the job to `PUBLISHED` and make the published URL available to the Frontend.

**Event:** `website.failed`

**Producer:** Website Generator / Publisher Module  
**Consumer:** Core Backend Service / Job Orchestrator  
**Technology:** Amazon SQS Standard  
**Queue:** `processing-results`

Published when generation or publishing fails (see section 7a).

**Messaging Considerations:**

Amazon SQS Standard provides at-least-once delivery.

Message consumers must implement idempotent processing to prevent duplicate operations.

In particular, repeated `profile.ready` messages must not create multiple websites for the same generation operation.

### 6.3 Internal API Endpoints

The following endpoints are used for communication between the Core Backend Service and Website Service.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/internal/websites/{websiteId}/preview` | Retrieve the generated website draft for preview |
| `POST` | `/internal/websites/{websiteId}/publish` | Accept publication of the approved website under the selected unique subdomain (returns `202`) |
| `POST` | `/internal/websites/{websiteId}/retry-generation` | Reset a failed generation so it can be retried |

#### GET — Website Preview

The Core Backend Service requests the generated draft using `websiteId`.

The Website Service retrieves the draft from PostgreSQL and returns it following the `WebsitePreview` schema (Shared Data Contracts §9.3). Errors use the standard `{ "error": { "code", "message", "requestId" } }` body (HTTP API Contracts §6).

The preview does not require a public subdomain.

#### POST — Publish Website

The Core Backend Service sends an authorized publishing request containing the user's selected subdomain slug.

**Example Request Body:**

```json
{
  "slug": "stefan-dobrincu"
}
```

**Accepting the request (synchronous part):**

1. Receive the publishing request.
2. Retrieve the approved website draft.
3. Validate the requested slug format.
4. Check whether the slug is reserved or already used.
5. Atomically reserve the slug in PostgreSQL, enforcing the unique constraint.
6. Set the website to `PUBLISHING` and write `website.publish.requested` to the outbox.
7. Return `202 Accepted`.

**Publishing (asynchronous part, on `website.publish.requested`):**

1. Re-validate the draft and slug reservation.
2. Call the render worker to produce the static files.
3. Upload the files to the corresponding S3 location, `index.html` last.
4. Update website metadata, status `PUBLISHED`, and public URL.
5. Publish the `website.published` event.

**Response — 202 Accepted** (HTTP API Contracts §3.4 and §4.2):

```json
{
  "websiteId": "website-456",
  "slug": "stefan-dobrincu",
  "status": "PUBLISHING"
}
```

Publishing is idempotent for the same website and slug: a repeated request returns `202` while publishing and `200` with the public URL once published. Publishing an already published website under a different slug is a conflict (`SLUG_CONFLICT`).

When publication completes, the website becomes accessible at `https://stefan-dobrincu.ourdomain.com` and the result reaches the Core Backend Service through `website.published`.

**Slug Conflict:**

If the selected slug is already taken or reserved by another user, the service rejects the request.

**Expected HTTP Status:** `409 Conflict`

```json
{
  "error": {
    "code": "SLUG_TAKEN",
    "message": "The requested subdomain is unavailable.",
    "requestId": "req-123"
  }
}
```

The user must select another available subdomain before publishing.

**Security:**

Internal endpoints are accessible only to authorized backend components.

The Core Backend Service is responsible for validating user identity and website ownership before forwarding requests.

Calls from the Core Backend are signed with HMAC service-to-service authentication. The Core Backend forwards the acting user in the `X-Actor-User-Id` header; this header is context only, not authentication, and the Website Service trusts it only from an authenticated internal caller (Communication Standards §6.6).

The Website Service must enforce slug uniqueness independently of frontend availability checks.

---

## 7. Website Service Happy Flow

1. The Website Generator receives a `profile.ready` message from the Amazon SQS `website-generation` queue.
2. It retrieves the unified profile and selected website template.
3. It calls the external AI provider to generate personalized website content.
4. The generated website draft is stored in PostgreSQL.
5. The Website Generator sends a `website.generated` message to the Amazon SQS `processing-results` queue.
6. The Core Backend Service retrieves the website draft for frontend preview.
7. The user reviews the generated website.
8. The user selects a preferred subdomain slug.
9. The user chooses Publish.
10. The Core Backend Service validates the user's authorization and sends the publishing request to the Website Publisher.
11. The Website Publisher retrieves the approved website draft.
12. The Publisher validates the selected slug and atomically reserves it using PostgreSQL's unique constraint.
13. The Publisher sets the website to `PUBLISHING`, queues `website.publish.requested` and returns `202`.
14. The Publisher consumes the event from the `website-publishing` queue and calls the render worker to prepare the static HTML, CSS and assets.
15. The generated files are uploaded to Amazon S3 under the corresponding slug prefix, `index.html` last.
16. The website publishing metadata, public URL and status are updated in PostgreSQL.
17. The Website Publisher sends a `website.published` message to the Amazon SQS `processing-results` queue.
18. The Core Backend Service sets the job to `PUBLISHED`; the frontend, which polls the job status, shows the published URL.
19. The website becomes accessible through Amazon CloudFront at its unique subdomain.

**Example Final URL:**

`https://stefan-dobrincu.ourdomain.com`

---

## 7a. Failure Handling

**Statuses and columns.** `websites.status` is `GENERATING`, `GENERATION_FAILED`, `PREVIEW_READY`, `PUBLISHING`, `PUBLISH_FAILED`, `PUBLISHED` or `UNPUBLISHED`. Failure-handling columns: `generation_lease_expires_at`, `error_code`, `error_message`. `UNIQUE(profile_id)` means one website per profile, and one profile per job.

**`website.failed`.** On a failure the service publishes `website.failed` to `processing-results` (SQS Event Contracts §6.4), then deletes the request message.

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

`websiteId` is absent when the failure happened before the row was created. A publish failure uses `stage = WEBSITE_PUBLISHING` (for example `PUBLISH_ASSET_ERROR`); the website becomes `PUBLISH_FAILED` and Core returns the job to `PREVIEW_READY`. A taken slug stays a `409 SLUG_TAKEN` HTTP response.

**Handling `profile.ready` without duplicates.**

1. Validate the message. A poison message is left unacknowledged and goes to the DLQ.
2. Verify, read-only, that the profile exists and belongs to `userId` and `jobId`.
3. Claim the generation atomically: `INSERT INTO websites (id, user_id, profile_id, template_id, status, generation_lease_expires_at) VALUES (..., 'GENERATING', now() + interval '15 min') ON CONFLICT (profile_id) DO NOTHING RETURNING id`.
4. If a row came back, this worker owns the generation: generate and validate the draft while extending visibility and renewing the lease, then `UPDATE websites SET draft_content = ..., status = 'PREVIEW_READY' WHERE id = :id AND status = 'GENERATING'`, publish `website.generated`, delete the message.
5. Otherwise read the existing row:
   - `PREVIEW_READY`, `PUBLISHING`, `PUBLISH_FAILED` or `PUBLISHED`: the work is done. Re-publish `website.generated` (idempotent in Core) and delete the message.
   - `GENERATION_FAILED`: the failure was already reported. Delete the message.
   - `GENERATING` with an unexpired lease: another worker is on it. Do **not** delete the message; set its visibility to the lease remainder.
   - `GENERATING` with an expired lease: the previous worker died. Take over with `UPDATE websites SET generation_lease_expires_at = now() + interval '15 min' WHERE id = :id AND status = 'GENERATING' AND generation_lease_expires_at < now()`. One updated row means this worker owns it; zero rows means re-evaluate.

A duplicate that arrives after completion does not regenerate anything or call the LLM again. The lease is 15 minutes.

**Retry of a failed generation.** The retry **reuses the same website row**. Core calls the internal `retry-generation` endpoint (HTTP API Contracts §4.3), which resets `GENERATION_FAILED → GENERATING` with a fresh lease, and then re-publishes `profile.ready` for the same `profileId`. A stale duplicate arriving later for a `GENERATION_FAILED` row is still just deleted.

**Publishing failures.** The publishing consumer reads `website-publishing` (with `website-publishing-dlq`). A failed publish sets the website to `PUBLISH_FAILED`, publishes `website.failed` with `stage = WEBSITE_PUBLISHING`, and Core returns the job to `PREVIEW_READY` so the user can try again. Because `index.html` is uploaded last and publishing is idempotent for the same website and slug, a repeated publish is safe.

**Retries.** External calls (the AI provider, the render worker, S3, PostgreSQL) are retried 3 times in-process (base 1 s, factor 2, jitter ±25%, cap 15 s). An LLM response that fails schema validation is retried up to 2 times, then fails as `AI_OUTPUT_INVALID`. Publishing has no automatic retry beyond that and is safe for the user to repeat for the same website and slug.

**Queue and DLQ.** The service consumes `website-generation` (visibility timeout 10 min, `maxReceiveCount` 3) with dead-letter queue `website-generation-dlq`. The Core DLQ listener marks the job and website failed with `RETRIES_EXHAUSTED` if a message lands there.

## 8. Architectural Notes

- Website Generator and Website Publisher are separate internal modules within the same deployable service.
- Website generation is asynchronous and event-driven.
- Publishing is requested through an authorized HTTP call that returns `202`, and is completed asynchronously through the `website-publishing` queue.
- Publishing requires explicit user approval.
- Subdomains are selected during publishing rather than registration.
- The user's display name and website slug are independent values.
- Each published website must have a globally unique slug.
- Slug uniqueness is guaranteed by PostgreSQL, not only by application-level availability checks.
- Reserved infrastructure subdomains cannot be used for portfolio websites.
- Generated drafts are stored in PostgreSQL.
- Published static website files are stored in Amazon S3.
- Static files are produced by a Node render worker packaged as an AWS Lambda container image.
- All user websites share one S3 bucket and one CloudFront distribution.
- Wildcard DNS and a wildcard TLS certificate support user subdomains.
- A CloudFront Function performs hostname-based routing to the correct website files.
- Public website requests are served through CloudFront without requiring execution of the Website Service.
- Amazon SQS Standard is used for asynchronous generation, publishing requests and completion events.
- SQS consumers must implement idempotent processing.
- Internal API endpoints are accessed through the Core Backend Service.
- HTTP contracts are defined in HTTP API Contracts, event payloads in SQS Event Contracts, and JSON schemas in Shared Data Contracts. Final SQL types, foreign keys across service boundaries and status constraints are finalized during Technical Design.
