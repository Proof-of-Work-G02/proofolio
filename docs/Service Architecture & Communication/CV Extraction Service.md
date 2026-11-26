# CV Extraction Service

**Service Type:** AI Processing Microservice

**Main Responsibility:** Extracting structured professional information from uploaded CV documents

**Scope:** Happy Flow only

---

## 1. Purpose

The CV Extraction Service is responsible for processing uploaded CV documents and transforming their contents into structured data that can be used to build a unified user profile.

The service receives extraction tasks asynchronously through Amazon SQS, retrieves the corresponding CV document from private Amazon S3 storage and extracts relevant professional information using document processing and AI-based extraction techniques.

The extracted information is structured into a consistent JSON format and made available to the Core Backend Service for profile aggregation.

The service operates independently from the other AI Processing Services and does not communicate directly with the Frontend.

**Main Responsibilities:**

- Consume CV extraction requests from Amazon SQS.
- Retrieve uploaded CV documents from private Amazon S3 storage.
- Extract textual content from CV documents.
- Identify and structure relevant professional information.
- Produce a standardized JSON extraction result.
- Make the extraction result available to the Core Backend Service.
- Send a `processing.completed` message through Amazon SQS.

---

## 2. Internal Modules

The CV Extraction Service is organized into three logical processing components.

These components belong to the same deployable service and are not independent microservices.

### 2.1 Document Processing Component

Responsible for retrieving and reading CV documents.

**Responsibilities:**

- Receive the document reference from the extraction request.
- Retrieve the CV document from Amazon S3.
- Read and extract the textual content from the document.
- Prepare the extracted text for structured information extraction.

**Inputs:**

- `jobId`
- `taskId`
- `userId`
- `cvS3Key` (object key relative to the configured uploads bucket)

**Outputs:**

- Extracted CV text

### 2.2 Information Extraction Component

Responsible for transforming CV text into structured professional information.

**Responsibilities:**

- Analyze the extracted CV text.
- Identify relevant professional and academic information.
- Organize extracted information into predefined categories.
- Normalize the extracted information into a consistent JSON structure.
- Preserve relevant details from the original CV.
- Avoid inventing information that is not supported by the document.

**Information Categories:**

| Category | Extracted Information |
| --- | --- |
| Personal Information | `fullName`, `email`, `phone`, `location`, `links` (flat fields in `profile`) |
| Professional Summary | `headline` and `summary`, when present in the CV |
| Education | Institutions, degrees, fields of study, dates |
| Work Experience | Companies, positions, responsibilities, dates |
| Projects | Project names, descriptions, technologies |
| Technical Skills | Programming languages, frameworks, tools |
| Certifications | Certifications and relevant qualifications |
| Languages | Languages and proficiency levels |
| Volunteering and Awards | Optional: `volunteering`, `awards` when the CV contains them |

The structure of the extraction result is defined by `CVExtractionResult` and `CanonicalProfessionalProfile` in Shared Data Contracts (§4 and §5).

Missing information should remain absent or explicitly represented as unavailable according to the agreed schema.

**Inputs:**

- Extracted CV text

**Outputs:**

- Structured CV information (JSON)

### 2.3 Result Delivery Component

Responsible for preparing and delivering the extraction result.

**Responsibilities:**

- Validate the extracted data against the agreed output schema.
- Store the extraction result in private storage when using reference-based result delivery.
- Prepare the processing completion message.
- Send the `processing.completed` message to Amazon SQS.
- Include the identifiers needed by the Core Backend Service to associate the result with the original processing task.

**Inputs:**

- `jobId`
- `taskId`
- Structured CV extraction result

**Outputs:**

- Available structured extraction result
- `processing.completed` message

---

## 3. Incoming Communication

The CV Extraction Service receives processing tasks asynchronously through Amazon SQS.

| Source | Technology | Purpose |
| --- | --- | --- |
| Core Backend Service / Job Orchestration Module | Amazon SQS (`cv-extraction`) | Receive `cv.extract.requested` messages |

**Communication Flow:**

1. The user uploads a CV through the Frontend.
2. The Core Backend Service validates the file and uploads it to private Amazon S3 storage.
3. The Job Orchestration Module creates the corresponding extraction task.
4. The Job Orchestration Module sends a `cv.extract.requested` message to the Amazon SQS `cv-extraction` queue.
5. The CV Extraction Service consumes the message and starts processing.

The service does not expose HTTP endpoints for the Happy Flow.

---

## 4. Outgoing Communication

| Destination | Protocol / Technology | Purpose |
| --- | --- | --- |
| Amazon S3 | AWS SDK / S3 API | Retrieve uploaded CV documents and store extraction output when required |
| AI Processing Component | Internal model inference / AI Provider API | Extract and structure professional information |
| Amazon SQS (`processing-results`) | AWS SDK / SQS API | Send `processing.completed` messages to Core Backend Service |

**Important Considerations:**

- Original CV documents are retrieved from private Amazon S3 storage.
- The service does not directly access the Core Backend Service database.
- The extracted information is returned through the agreed result-delivery mechanism.
- Amazon SQS messages carry processing identifiers and references rather than original CV documents.
- The AI model and extraction framework will be selected during implementation design.
- The service does not communicate directly with the Website Service.

---

## 5. Data Ownership

The CV Extraction Service processes CV documents and produces structured extraction results.

It does not own user accounts, processing jobs or unified profiles.

### 5.1 Amazon S3 — Input Documents

Original CV files are stored by the Core Backend Service in private Amazon S3 storage.

**Example input structure:**

```
portfolio-uploads/
  user-123/
    job-456/
      cv.pdf
```

The CV Extraction Service retrieves documents using the references received through Amazon SQS.

It requires read access only to the relevant uploaded documents.

### 5.2 Structured Extraction Results

The service produces a JSON document containing the extracted CV information.

**Contract:** `CVExtractionResult` (Shared Data Contracts §5). The service writes one JSON document containing the common result fields plus a `profile` object that follows `CanonicalProfessionalProfile` (Shared Data Contracts §4).

```json
{
  "schemaVersion": 1,
  "jobId": "job-456",
  "taskId": "task-789",
  "sourceType": "CV",
  "profile": {
    "fullName": "Alex Popescu",
    "email": "alex@example.com",
    "location": "Cluj-Napoca, Romania",
    "summary": "Computer Science student interested in backend development.",
    "workExperience": [
      {
        "company": "Example Company",
        "position": "Software Developer Intern",
        "description": "Developed backend functionality using Java.",
        "startDate": "2026-07",
        "endDate": "2026-09",
        "isCurrent": false
      }
    ],
    "education": [
      {
        "institution": "Example University",
        "degree": "Bachelor's Degree",
        "fieldOfStudy": "Computer Science",
        "startDate": "2024",
        "endDate": "2027"
      }
    ],
    "skills": ["Java", "Python", "PostgreSQL"],
    "projects": [
      {
        "name": "Portfolio Platform",
        "description": "Personal portfolio generation application.",
        "technologies": ["Java", "React"]
      }
    ]
  }
}
```

- Personal details are **flat fields inside `profile`** (`fullName`, `email`, `phone`, `location`, `links`), not a `personalInfo` object.
- Dates keep the precision found in the CV (`YYYY`, `YYYY-MM` or `YYYY-MM-DD`); `endDate` being absent does not imply `isCurrent: true`.
- Unknown optional fields are omitted. An empty array is used only when the CV explicitly shows an empty category (Shared Data Contracts §4.8).

The structured JSON is stored in private Amazon S3 storage.

**Example output structure:**

```
extraction-results/
  job-456/
    task-789/
      cv.json
```

The completion message contains the object key of this result in `resultS3Key` (`job-456/task-789/cv.json`). The key is relative to the configured `extraction-results` bucket; consumers must not prepend a bucket name (Shared Data Contracts §10.2).

The Core Backend Service remains responsible for recording the extraction result in its `extraction_results` table and using the data during profile aggregation.

The result storage and referencing contract is defined in SQS Event Contracts §5.1 and Shared Data Contracts §5 and §10. Core Backend stores the S3 key in `extraction_results.result_s3_key` (see Core Backend Service).

---

## 6. Events & API Endpoints

### 6.1 Consumed Events

**Event:** `cv.extract.requested`

**Producer:** Core Backend Service / Job Orchestration Module  
**Consumer:** CV Extraction Service  
**Technology:** Amazon SQS Standard  
**Queue:** `cv-extraction`

Triggered when the Core Backend Service creates a CV extraction task.

**Example Payload:**

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

The CV Extraction Service uses `cvS3Key` to retrieve the uploaded CV from the configured S3 bucket.

### 6.2 Published Events

**Event:** `processing.completed`

**Producer:** CV Extraction Service  
**Consumer:** Core Backend Service / Job Orchestration Module  
**Technology:** Amazon SQS Standard  
**Queue:** `processing-results`

Published after the CV has been successfully processed and the structured extraction result is available.

**Example Payload:**

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

The Core Backend Service uses `jobId` and `taskId` to identify the corresponding processing task.

It retrieves the extraction result, records it and updates the task status in PostgreSQL.

The Job Orchestration Module then checks whether all requested processing tasks have completed.

### 6.3 Internal API Endpoints

The CV Extraction Service does not expose HTTP endpoints as part of the Happy Flow.

All processing requests and completion notifications are exchanged asynchronously through Amazon SQS.

---

## 7. CV Extraction Service Happy Flow

1. The Core Backend Service receives the user's uploaded CV.
2. The Ingestion Module validates the document and stores it in private Amazon S3 storage.
3. The Job Orchestration Module creates a CV extraction task.
4. The Job Orchestration Module sends a `cv.extract.requested` message to the Amazon SQS `cv-extraction` queue.
5. The CV Extraction Service consumes the message.
6. The Document Processing Component retrieves the CV document from Amazon S3.
7. The document text is extracted and prepared for processing.
8. The Information Extraction Component analyzes the CV content and identifies relevant professional information.
9. The extracted information is normalized into a structured JSON format.
10. The Result Delivery Component validates the generated JSON against the agreed schema.
11. The extraction result is stored in private Amazon S3 storage.
12. The CV Extraction Service sends a `processing.completed` message to the Amazon SQS `processing-results` queue.
13. The Core Backend Service consumes the message and retrieves the structured extraction result.
14. The Job Orchestration Module updates the processing task status in PostgreSQL.
15. The extracted CV information becomes available to the Profile Aggregation Module when all requested processing tasks are complete.

---

## 7a. Failure Handling

**Failure events.** When the task cannot succeed (a permanent business failure, or retries exhausted) the service publishes `processing.failed` to `processing-results` with `stage = CV_EXTRACTION`, `sourceType = CV`, an `errorCode` (for example `SOURCE_UNREADABLE`, `SOURCE_EMPTY`, `AI_OUTPUT_INVALID`), a user-safe `errorMessage`, `retryable` and `attempts` (Shared Data Contracts §3.3; SQS Event Contracts §5.2).

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

**The CV is the required source.** A `FAILED` CV task fails the whole job, so a CV failure is the one that matters most to the user.

**Rules**

- Publish the failure event first, then delete the request message. If publishing fails, do not delete the message; it is redelivered.
- Never write a partial result to S3. Never include personal data in `errorMessage` or logs.
- Echo the request's optional `attempt` in completion and failure events.
- Idempotent by `taskId`; Core ignores a failure for an already `COMPLETED` task.

**Retries.** Each external call is retried in-process 3 times (base 1 s, factor 2, jitter ±25%, cap 15 s, `Retry-After` respected). An LLM response that fails schema validation is retried up to 2 times; after that it is a permanent `AI_OUTPUT_INVALID` failure.

**Queue and DLQ.** The service consumes `cv-extraction` (visibility timeout 5 min, `maxReceiveCount` 3) with dead-letter queue `cv-extraction-dlq`. Poison messages (malformed JSON, unsupported `schemaVersion`, missing required field, unknown `jobId`) are not processed and no failure event is sent; they reach the DLQ, and the Core DLQ listener marks the task failed with `RETRIES_EXHAUSTED`. Workers extend visibility while they are still making progress.

## 8. Architectural Notes

- The CV Extraction Service is independently deployable.
- The service is implemented in Python.
- Processing is asynchronous and event-driven through Amazon SQS Standard.
- The service has one clearly defined responsibility: extracting structured information from CV documents.
- The internal processing components are not separate microservices.
- The service does not expose HTTP endpoints for the Happy Flow.
- The service does not directly modify the Core Backend Service database.
- Amazon S3 is used for private document storage and reference-based result delivery.
- The extraction output must follow the `CVExtractionResult` JSON Schema (`schemaVersion: 1`), which embeds `CanonicalProfessionalProfile`.
- The service must preserve the meaning of the original CV and avoid generating unsupported professional information.
- SQS consumers must support idempotent processing because messages may be delivered more than once.
- Sensitive CV information must not be included in application logs or unnecessary message payloads.
- CV content is treated as untrusted input, including when processed by an AI model.
