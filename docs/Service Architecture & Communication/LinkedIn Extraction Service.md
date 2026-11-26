# LinkedIn Extraction Service

**Service Type:** AI Processing Microservice  
**Main Responsibility:** Extracting structured professional information from user-provided LinkedIn profile data

**Scope:** Happy Flow — User-Provided LinkedIn PDF

---

## 1. Purpose

The LinkedIn Extraction Service is responsible for transforming user-provided LinkedIn profile information into structured professional data.

For the initial implementation, users provide an exported PDF of their LinkedIn profile. The service retrieves the uploaded document from private Amazon S3 storage, extracts its contents and organizes relevant professional information into a structured JSON format.

The extracted information is subsequently combined with CV and GitHub analysis results by the Profile Aggregation Module.

The service receives processing requests asynchronously through Amazon SQS and communicates processing completion through the shared results queue.

**Main Responsibilities:**

- Consume LinkedIn extraction requests from Amazon SQS.
- Retrieve user-provided LinkedIn PDF documents from private Amazon S3 storage.
- Extract textual information from the uploaded documents.
- Identify relevant professional information.
- Normalize extracted information into structured JSON.
- Make the extraction result available to the Core Backend Service.
- Publish a `processing.completed` message through Amazon SQS.

**MVP Scope:**

The initial implementation relies on LinkedIn information explicitly exported and uploaded by the user.

The service does not automatically scrape LinkedIn profiles, access user accounts or require LinkedIn API authentication.

---

## 2. Internal Modules

The LinkedIn Extraction Service is organized into three logical processing components.

These components belong to the same deployable service and are not independent microservices.

### 2.1 Document Processing Component

Responsible for retrieving and reading uploaded LinkedIn documents.

**Responsibilities:**

- Receive the LinkedIn document reference from the processing request.
- Retrieve the uploaded PDF from Amazon S3.
- Extract textual content from the document.
- Prepare the extracted information for structured processing.

**Inputs:**

- `jobId`
- `taskId`
- `userId`
- `linkedinS3Key` (object key relative to the configured uploads bucket)

**Outputs:**

- Extracted LinkedIn profile text

### 2.2 Information Extraction Component

Responsible for identifying and structuring professional information from the LinkedIn document.

**Responsibilities:**

- Analyze the extracted profile text.
- Identify professional and academic information.
- Extract professional experience, skills and relevant achievements.
- Normalize the information into predefined categories.
- Preserve relevant details from the original document.
- Avoid inventing information not supported by the provided profile.
- Produce a consistent JSON structure compatible with the Profile Aggregation Module.

**Information Categories:**

| Category | Extracted Information |
| --- | --- |
| Personal Information | `fullName`, `headline`, `location`, `links` (profile URL when available) |
| Professional Summary | `summary` (LinkedIn About section and professional description) |
| Work Experience | `workExperience`: company, position, description, dates |
| Education | `education`: institution, degree, field of study, dates |
| Skills | `skills` |
| Certifications | `certifications`: name, issuer, date |
| Projects | `projects` |
| Volunteering | `volunteering`: organization, role, description, dates |
| Languages | `languages`: name, proficiency |
| Achievements | `awards`: name, issuer, date, description |

Only information present in the uploaded document should be extracted.

The service must not assume that every LinkedIn profile contains all categories.

**Inputs:**

- Extracted LinkedIn profile text

**Outputs:**

- Structured LinkedIn profile information (JSON)

### 2.3 Result Delivery Component

Responsible for validating and delivering the structured extraction result.

**Responsibilities:**

- Validate the extracted information against the agreed JSON schema.
- Store the structured extraction result in private Amazon S3 storage.
- Prepare the processing completion message.
- Publish a `processing.completed` event to Amazon SQS.
- Include the identifiers required to associate the result with its processing task.

**Inputs:**

- `jobId`
- `taskId`
- Structured LinkedIn extraction result

**Outputs:**

- Stored extraction result
- `processing.completed` message

---

## 3. Incoming Communication

The LinkedIn Extraction Service receives processing tasks asynchronously through Amazon SQS.

| Source | Technology | Purpose |
| --- | --- | --- |
| Core Backend Service / Job Orchestration Module | Amazon SQS (`linkedin-extraction`) | Receive `linkedin.extract.requested` messages |

**Communication Flow:**

1. The user uploads an exported LinkedIn profile PDF through the Frontend.
2. The Core Backend Service validates the uploaded document.
3. The Ingestion Module stores the document in private Amazon S3 storage.
4. The Job Orchestration Module creates a LinkedIn extraction task.
5. The Job Orchestration Module sends a `linkedin.extract.requested` message to the Amazon SQS `linkedin-extraction` queue.
6. The LinkedIn Extraction Service consumes the message and starts processing.

The service does not expose HTTP endpoints for the Happy Flow.

---

## 4. Outgoing Communication

| Destination | Protocol / Technology | Purpose |
| --- | --- | --- |
| Amazon S3 | AWS SDK / S3 API | Retrieve uploaded LinkedIn documents and store structured extraction results |
| AI Provider / Extraction Component | Internal processing / HTTPS API | Extract and structure professional information |
| Amazon SQS (`processing-results`) | AWS SDK / SQS API | Send `processing.completed` messages to Core Backend Service |

**Important Considerations:**

- LinkedIn documents are uploaded by the user and stored privately.
- The service does not directly communicate with LinkedIn during the MVP Happy Flow.
- The service does not directly access the Core Backend PostgreSQL database.
- The service does not communicate directly with the Website Service.
- The extracted information is delivered through private storage and SQS completion messages.
- The AI model and document processing framework will be selected during implementation design.

---

## 5. Data Ownership

The LinkedIn Extraction Service processes user-provided LinkedIn documents and produces structured extraction results.

It does not own user accounts, processing jobs or unified user profiles.

### 5.1 Amazon S3 — Input Documents

The Core Backend Service stores uploaded LinkedIn documents in private Amazon S3 storage.

**Example Structure:**

```
portfolio-uploads/
  user-123/
    job-456/
      linkedin-profile.pdf
```

The LinkedIn Extraction Service retrieves the document using the S3 reference received through Amazon SQS.

It requires read access only to the relevant input document.

### 5.2 Structured Extraction Results

The service produces a JSON document containing the extracted professional information.

**Contract:** `LinkedInExtractionResult` (Shared Data Contracts §6). It uses the same `CanonicalProfessionalProfile` as the CV Extraction Service, so the Profile Aggregation Module does not need a separate model.

```json
{
  "schemaVersion": 1,
  "jobId": "job-456",
  "taskId": "task-791",
  "sourceType": "LINKEDIN",
  "profile": {
    "fullName": "Alex Popescu",
    "headline": "Software Engineering Student",
    "location": "Cluj-Napoca, Romania",
    "summary": "Interested in backend engineering and AI systems.",
    "workExperience": [
      {
        "company": "Example Company",
        "position": "Software Developer Intern",
        "description": "Worked on backend development.",
        "startDate": "2026-07",
        "endDate": "2026-09"
      }
    ],
    "education": [
      {
        "institution": "Example University",
        "degree": "Bachelor's Degree",
        "fieldOfStudy": "Computer Science"
      }
    ],
    "skills": ["Java", "Spring Boot", "PostgreSQL"],
    "certifications": []
  }
}
```

Only the `profile` object nests the professional data; the top level holds `schemaVersion`, `jobId`, `taskId` and `sourceType`. Source evidence for aggregation is carried through `taskId` and `sourceType`, which the Profile Aggregation Module uses to build `provenance` entries.

### 5.3 Amazon S3 — Extraction Results

The structured extraction result is stored in private Amazon S3 storage.

**Example Structure:**

```
extraction-results/
  job-456/
    task-791/
      linkedin.json
```

The Core Backend Service receives the object key of this result in `resultS3Key` (`job-456/task-791/linkedin.json`) through Amazon SQS. The key is relative to the configured `extraction-results` bucket.

It retrieves the extracted information and records the corresponding extraction result.

The Profile Aggregation Module uses the LinkedIn information together with the other available sources to create the unified user profile.

---

## 6. Events & API Endpoints

### 6.1 Consumed Events

**Event:** `linkedin.extract.requested`

**Producer:** Core Backend Service / Job Orchestration Module  
**Consumer:** LinkedIn Extraction Service  
**Technology:** Amazon SQS Standard  
**Queue:** `linkedin-extraction`

Triggered when the Core Backend Service creates a LinkedIn extraction task.

**Example Payload:**

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

The service retrieves the uploaded document from the configured private S3 bucket and starts extraction.

### 6.2 Published Events

**Event:** `processing.completed`

**Producer:** LinkedIn Extraction Service  
**Consumer:** Core Backend Service / Job Orchestration Module  
**Technology:** Amazon SQS Standard  
**Queue:** `processing-results`

Published after the LinkedIn document has been successfully processed and the structured result is available.

**Example Payload:**

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440008",
  "event": "processing.completed",
  "occurredAt": "2026-11-17T14:31:30Z",
  "jobId": "job-456",
  "taskId": "task-791",
  "sourceType": "LINKEDIN",
  "status": "COMPLETED",
  "resultS3Key": "job-456/task-791/linkedin.json"
}
```

The Core Backend Service identifies the corresponding task and retrieves the structured extraction result.

The Job Orchestration Module updates the processing task status and checks whether all requested processing tasks have completed.

### 6.3 Internal API Endpoints

The LinkedIn Extraction Service does not expose HTTP endpoints as part of the Happy Flow.

All processing requests and completion notifications are exchanged asynchronously through Amazon SQS.

---

## 7. LinkedIn Extraction Service Happy Flow

1. The user exports their LinkedIn profile as a PDF.
2. The user uploads the exported document through the Frontend.
3. The Core Backend Service validates the document and uploads it to private Amazon S3 storage.
4. The Job Orchestration Module creates a LinkedIn extraction task.
5. The Job Orchestration Module sends a `linkedin.extract.requested` message to the Amazon SQS `linkedin-extraction` queue.
6. The LinkedIn Extraction Service consumes the message.
7. The Document Processing Component retrieves the LinkedIn PDF from Amazon S3.
8. The document text is extracted and prepared for processing.
9. The Information Extraction Component identifies professional experience, education, skills and other relevant profile information.
10. The extracted information is normalized into a structured JSON format.
11. The Result Delivery Component validates the JSON against the agreed schema.
12. The extraction result is stored in private Amazon S3 storage.
13. The LinkedIn Extraction Service sends a `processing.completed` message to the Amazon SQS `processing-results` queue.
14. The Core Backend Service consumes the message and retrieves the structured extraction result.
15. The Job Orchestration Module updates the processing task status in PostgreSQL.
16. The LinkedIn information becomes available to the Profile Aggregation Module when all requested processing tasks have completed.

---

## 7a. Failure Handling

**Failure events.** When the task cannot succeed (a permanent business failure, or retries exhausted) the service publishes `processing.failed` to `processing-results` with `stage = LINKEDIN_EXTRACTION`, `sourceType = LINKEDIN`, an `errorCode` (for example `SOURCE_UNREADABLE`, `SOURCE_EMPTY`, `AI_OUTPUT_INVALID`), a user-safe `errorMessage`, `retryable` and `attempts` (Shared Data Contracts §3.3; SQS Event Contracts §5.2).

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440010",
  "event": "processing.failed",
  "occurredAt": "2026-11-17T14:31:00Z",
  "jobId": "job-456",
  "taskId": "task-789",
  "userId": "user-123",
  "sourceType": "LINKEDIN",
  "stage": "LINKEDIN_EXTRACTION",
  "errorCode": "SOURCE_UNREADABLE",
  "errorMessage": "The LinkedIn PDF could not be read.",
  "retryable": false,
  "attempts": 1
}
```

**LinkedIn is an optional source.** A `FAILED` LinkedIn task does not fail the job. The Core Backend leaves LinkedIn out of the profile, adds a warning, and continues from the CV.

**Rules**

- Publish the failure event first, then delete the request message. If publishing fails, do not delete the message; it is redelivered.
- Never write a partial result to S3. Never include personal data in `errorMessage` or logs.
- Echo the request's optional `attempt` in completion and failure events.
- Idempotent by `taskId`; Core ignores a failure for an already `COMPLETED` task.

**Retries.** Each external call is retried in-process 3 times (base 1 s, factor 2, jitter ±25%, cap 15 s, `Retry-After` respected). An LLM response that fails schema validation is retried up to 2 times; after that it is a permanent `AI_OUTPUT_INVALID` failure.

**Queue and DLQ.** The service consumes `linkedin-extraction` (visibility timeout 5 min, `maxReceiveCount` 3) with dead-letter queue `linkedin-extraction-dlq`. Poison messages (malformed JSON, unsupported `schemaVersion`, missing required field, unknown `jobId`) are not processed and no failure event is sent; they reach the DLQ, and the Core DLQ listener marks the task failed with `RETRIES_EXHAUSTED`. Workers extend visibility while they are still making progress.

## 8. Architectural Notes

- The LinkedIn Extraction Service is independently deployable.
- The service is implemented in Python.
- Processing is asynchronous and event-driven through Amazon SQS Standard.
- The MVP processes LinkedIn profile PDF documents explicitly provided by users.
- The service does not require LinkedIn OAuth authentication or automated profile scraping.
- LinkedIn profile URLs alone are not used as extraction inputs.
- The internal processing components are not separate microservices.
- The service does not expose HTTP endpoints for the Happy Flow.
- The service does not directly modify the Core Backend PostgreSQL database.
- Amazon S3 is used for private document storage and structured result delivery.
- The extraction output must follow the `LinkedInExtractionResult` JSON Schema (`schemaVersion: 1`), which embeds `CanonicalProfessionalProfile`.
- Extracted information must remain faithful to the original LinkedIn document.
- The service must not invent professional experience, skills or achievements.
- Unknown optional fields are omitted; an empty array is written only when the document explicitly shows an empty category (Shared Data Contracts §4.8). Date precision (`YYYY`, `YYYY-MM`, `YYYY-MM-DD`) is preserved.
- SQS consumers must implement idempotent processing to handle duplicate message deliveries.
- Uploaded documents and extracted personal information must be protected against unauthorized access.
- If an external AI provider processes profile content, the data transfer must comply with the application's privacy requirements and user consent.
- Document contents must be treated as untrusted input when passed to an AI model.
