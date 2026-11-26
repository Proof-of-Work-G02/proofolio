# GitHub Analysis Service

**Service Type:** AI Processing Microservice  
**Main Responsibility:** Extracting structured project and technical information from GitHub repositories

**Scope:** Happy Flow — Public Repository Analysis

---

## 1. Purpose

The GitHub Analysis Service is responsible for analyzing a user's GitHub repositories and extracting relevant information about their software projects, technical skills and development experience.

The service communicates with GitHub through its API to retrieve repository metadata, directory structures, file names and README documentation.

The extracted information is transformed into structured JSON data that can be combined with CV and LinkedIn extraction results to create a unified user profile.

For the initial implementation, **analysis is limited to public repositories and does not require cloning repositories or executing source code**.

The service receives processing requests asynchronously through Amazon SQS and returns processing results to the Core Backend Service.

**Main Responsibilities:**

- Consume GitHub analysis requests from Amazon SQS.
- Retrieve public repositories associated with a GitHub username.
- Retrieve repository metadata.
- Analyze directory structures and file names.
- Retrieve and analyze README documentation.
- Extract project descriptions, technologies and relevant technical information.
- Produce structured JSON results.
- Make the analysis results available to the Core Backend Service.
- Publish a `processing.completed` message through Amazon SQS.

---

## 2. Internal Modules

The service is organized into three logical processing components.

These components belong to the same deployable service and are not independent microservices.

### 2.1 GitHub API Integration Component

Responsible for communicating with GitHub and retrieving repository information.

**Responsibilities:**

- Receive the normalized `githubUsername` from the processing request (the Core Backend normalizes any submitted profile URL).
- Resolve the GitHub account.
- Retrieve the user's public repositories.
- Retrieve repository metadata.
- Retrieve the repository directory and file structure.
- Retrieve README documentation when available.
- Handle API pagination and respect GitHub API rate limits.

**Inputs:**

- `jobId`
- `taskId`
- `userId`
- `githubUsername` (normalized by the Core Backend)

**Outputs:**

- Repository list
- Repository metadata
- Directory and file structures
- README content

**Authentication to GitHub**

The service uses one server-side, read-only credential (a GitHub App installation token or a fine-grained read-only token) kept in the secret manager. No user OAuth token is stored or used, no extra GitHub scope is requested at login, and the `github.analyze.requested` event carries no token or token reference. The service handles GitHub rate limits and caches responses where it helps.

Access is read-only with minimal permissions. Access to private repositories is not required for the initial Happy Flow.

### 2.2 Repository Analysis Component

Responsible for interpreting retrieved repository information.

**Responsibilities:**

- Analyze repository metadata.
- Examine directory structures and file names.
- Analyze README documentation.
- Identify project names and descriptions.
- Extract technologies explicitly mentioned in README files.
- Identify technologies suggested by repository structure and configuration file names.
- Extract documented project features and functionality.
- Organize the collected information into a consistent JSON structure.
- Distinguish confirmed information from inferred information using `certainty` (`OBSERVED` / `INFERRED`) and attach `evidence` to each technology.

**Information Categories:**

| Category | Extracted Information |
| --- | --- |
| Repository Information | Name, description, URL, primary language (public repositories only; the schema has no `visibility` field) |
| Project Description | Purpose, functionality and project overview |
| Technologies | Programming languages, frameworks, databases and tools |
| Project Structure | Main directories and relevant file names |
| Features | Functionalities documented in README |
| Technical Evidence | `evidence[]` per technology: `GITHUB_METADATA`, `FILE_PATH` or `README` entries supporting identification |

**Analysis Approach:**

The initial analysis uses three primary information sources.

**Source 1: Repository Metadata**

Information provided directly by GitHub, such as repository names, descriptions, primary languages and repository URLs.

**Source 2: Directory Structure and File Names**

Repository structures and recognizable file names can provide indications about the technologies used.

For example:

```
portfolio-api/
  src/
    main/
      java/
  pom.xml
  Dockerfile
  README.md
```

From this structure, the analyzer can identify evidence suggesting:

- Java as a programming language.
- Maven as a build tool.
- Docker configuration.

Such observations should not automatically be treated as proof of specific frameworks or architectural patterns.

**Source 3: README Documentation**

README files can provide higher-level information about:

- Project purpose.
- Main features.
- Technologies and frameworks.
- Architecture descriptions.
- Deployment information.
- Project functionality.

AI-based extraction may be used to transform this documentation into structured project information.

**Inputs:**

- Repository metadata
- Repository directory structures
- Relevant file names
- README content

**Outputs:**

- Structured GitHub analysis result (JSON)

### 2.3 Result Delivery Component

Responsible for validating and delivering the analysis result.

**Responsibilities:**

- Validate the generated JSON against the agreed output schema.
- Store the analysis result in private Amazon S3 storage.
- Prepare the processing completion message.
- Publish a `processing.completed` event to Amazon SQS.
- Include the identifiers required to associate the result with the original task.

**Inputs:**

- `jobId`
- `taskId`
- Structured GitHub analysis result

**Outputs:**

- Stored analysis result
- `processing.completed` message

---

## 3. Incoming Communication

The GitHub Analysis Service receives processing requests asynchronously through Amazon SQS.

| Source | Technology | Purpose |
| --- | --- | --- |
| Core Backend Service / Job Orchestration Module | Amazon SQS (`github-analysis`) | Receive `github.analyze.requested` messages |

**Communication Flow:**

1. The user provides their GitHub username or profile URL through the Frontend.
2. The Core Backend Service validates the submitted information and normalizes it to a GitHub username.
3. The Job Orchestration Module creates a GitHub analysis task.
4. The Job Orchestration Module sends a `github.analyze.requested` message to the Amazon SQS `github-analysis` queue.
5. The GitHub Analysis Service consumes the message and starts repository analysis.

The service does not expose HTTP endpoints for the Happy Flow.

---

## 4. Outgoing Communication

| Destination | Protocol / Technology | Purpose |
| --- | --- | --- |
| GitHub API | HTTPS REST API | Retrieve repositories, metadata, file structures and README content |
| AI Provider / Analysis Component | Internal processing / HTTPS API | Extract structured information from repository data |
| Amazon S3 | AWS SDK / S3 API | Store structured analysis results |
| Amazon SQS (`processing-results`) | AWS SDK / SQS API | Send `processing.completed` messages to Core Backend Service |

**Important Considerations:**

- GitHub is the source of repository metadata and documentation.
- The initial implementation retrieves information through GitHub APIs.
- Repository cloning is not required.
- Source code execution is not required.
- The service does not modify GitHub repositories.
- The service does not directly access the Core Backend PostgreSQL database.
- The service does not communicate directly with Website Service.
- AI processing is used to structure and interpret the retrieved information, not to invent unsupported project details.

---

## 5. Data Ownership

The GitHub Analysis Service processes repository information and produces structured project analysis results.

It does not own user accounts, processing jobs or unified user profiles.

### 5.1 GitHub Repository Data

Repository information is retrieved through the GitHub API.

The initial implementation uses publicly available repository information.

**Relevant Data:**

- Repository name
- Repository URL
- Repository description
- Primary programming language
- Repository structure
- File and directory names
- README documentation

The service does not store complete repository clones.

### 5.2 Structured Analysis Results

The service produces structured JSON containing information about the analyzed repositories.

**Contract:** `GitHubAnalysisResult` (Shared Data Contracts §7). Unlike CV and LinkedIn, the result is repository-oriented and does not use `CanonicalProfessionalProfile`.

```json
{
  "schemaVersion": 1,
  "jobId": "job-456",
  "taskId": "task-790",
  "sourceType": "GITHUB",
  "githubUsername": "example-user",
  "repositories": [
    {
      "name": "portfolio-api",
      "url": "https://github.com/example-user/portfolio-api",
      "description": "Backend API for a portfolio application.",
      "primaryLanguage": "Java",
      "technologies": [
        {
          "name": "Java",
          "certainty": "OBSERVED",
          "evidence": [{ "kind": "GITHUB_METADATA", "reference": "primaryLanguage" }]
        },
        {
          "name": "Maven",
          "certainty": "INFERRED",
          "evidence": [{ "kind": "FILE_PATH", "path": "pom.xml" }]
        }
      ],
      "features": ["User authentication", "Portfolio management"],
      "structure": ["src/main/java/", "pom.xml", "Dockerfile", "README.md"],
      "projectSummary": "A Java backend project for managing portfolio information."
    }
  ]
}
```

- Each technology is an **object** with `name`, `certainty` (`OBSERVED` or `INFERRED`) and `evidence[]`, not a plain string. `OBSERVED` means GitHub metadata or inspected documentation states it directly; `INFERRED` means it is suggested by structure or file names (for example `pom.xml` suggests Maven).
- Evidence `kind` values: `GITHUB_METADATA`, `FILE_PATH`, `README`. Optional evidence fields: `path`, `reference`, `url`.
- An `INFERRED` technology must not be promoted to a verified skill without an agreed evidence policy.
- Required repository fields are `name` and `url`; the rest are optional.

### 5.3 Amazon S3

The structured analysis result is stored in private Amazon S3 storage.

**Example Structure:**

```
extraction-results/
  job-456/
    task-790/
      github.json
```

The Core Backend Service receives the object key of the result in `resultS3Key` (`job-456/task-790/github.json`) through Amazon SQS. The key is relative to the configured `extraction-results` bucket.

It retrieves the analysis output and records the corresponding extraction result.

The Profile Aggregation Module subsequently combines the GitHub information with the available CV and LinkedIn results.

---

## 6. Events & API Endpoints

### 6.1 Consumed Events

**Event:** `github.analyze.requested`

**Producer:** Core Backend Service / Job Orchestration Module  
**Consumer:** GitHub Analysis Service  
**Technology:** Amazon SQS Standard  
**Queue:** `github-analysis`

Triggered when a GitHub analysis task is created.

**Example Payload:**

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

The service uses `githubUsername` to retrieve the user's public repository information.

### 6.2 Published Events

**Event:** `processing.completed`

**Producer:** GitHub Analysis Service  
**Consumer:** Core Backend Service / Job Orchestration Module  
**Technology:** Amazon SQS Standard  
**Queue:** `processing-results`

Published after repository analysis has completed and the structured result is available.

**Example Payload:**

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440009",
  "event": "processing.completed",
  "occurredAt": "2026-11-17T14:31:45Z",
  "jobId": "job-456",
  "taskId": "task-790",
  "sourceType": "GITHUB",
  "status": "COMPLETED",
  "resultS3Key": "job-456/task-790/github.json"
}
```

The Core Backend Service identifies the corresponding task and retrieves the structured analysis result.

The Job Orchestration Module updates the task status and checks whether all requested processing tasks have completed.

### 6.3 Internal API Endpoints

The GitHub Analysis Service does not expose HTTP endpoints as part of the Happy Flow.

Processing requests and completion messages are exchanged asynchronously through Amazon SQS.

GitHub API requests are outbound HTTPS calls to an external service, not internal endpoints exposed by this microservice.

---

## 7. GitHub Analysis Service Happy Flow

1. The user submits their GitHub username or profile URL through the Frontend.
2. The Core Backend Service validates the information and creates a GitHub analysis task.
3. The Job Orchestration Module sends a `github.analyze.requested` message to the Amazon SQS `github-analysis` queue.
4. The GitHub Analysis Service consumes the message.
5. The GitHub API Integration Component retrieves the user's public repositories through the GitHub API.
6. For each repository, the service retrieves relevant metadata.
7. The service retrieves the repository directory structure and file names.
8. The service retrieves README documentation when available.
9. The Repository Analysis Component examines the retrieved information.
10. The component extracts project descriptions, technologies, features and other relevant professional information.
11. The extracted information is transformed into structured JSON.
12. The Result Delivery Component validates the result against the agreed schema.
13. The analysis result is stored in private Amazon S3 storage.
14. The service sends a `processing.completed` message to the Amazon SQS `processing-results` queue.
15. The Core Backend Service consumes the event and retrieves the stored analysis result.
16. The Job Orchestration Module updates the processing task status.
17. The GitHub analysis result becomes available to the Profile Aggregation Module.

---

## 7a. Failure Handling

**Failure events.** When the task cannot succeed (a permanent business failure, or retries exhausted) the service publishes `processing.failed` to `processing-results` with `stage = GITHUB_ANALYSIS`, `sourceType = GITHUB`, an `errorCode` (for example `SOURCE_NOT_FOUND`, `EXTERNAL_RATE_LIMITED`, `AI_OUTPUT_INVALID`), a user-safe `errorMessage`, `retryable` and `attempts` (Shared Data Contracts §3.3; SQS Event Contracts §5.2).

```json
{
  "schemaVersion": 1,
  "eventId": "550e8400-e29b-41d4-a716-446655440010",
  "event": "processing.failed",
  "occurredAt": "2026-11-17T14:31:00Z",
  "jobId": "job-456",
  "taskId": "task-789",
  "userId": "user-123",
  "sourceType": "GITHUB",
  "stage": "GITHUB_ANALYSIS",
  "errorCode": "SOURCE_NOT_FOUND",
  "errorMessage": "The GitHub user could not be found.",
  "retryable": false,
  "attempts": 1
}
```

**GitHub is an optional source.** A `FAILED` GitHub task does not fail the job. The Core Backend leaves GitHub out of the profile, adds a warning, and continues from the CV.

**Rules**

- Publish the failure event first, then delete the request message. If publishing fails, do not delete the message; it is redelivered.
- Never write a partial result to S3. Never include personal data in `errorMessage` or logs.
- Echo the request's optional `attempt` in completion and failure events.
- Idempotent by `taskId`; Core ignores a failure for an already `COMPLETED` task.

**Retries.** Each external call is retried in-process 3 times (base 1 s, factor 2, jitter ±25%, cap 15 s, `Retry-After` respected). On a GitHub rate limit the service waits up to 60 s, as GitHub's guidance allows, before giving up with `EXTERNAL_RATE_LIMITED`. An LLM response that fails schema validation is retried up to 2 times; after that it is a permanent `AI_OUTPUT_INVALID` failure.

**Queue and DLQ.** The service consumes `github-analysis` (visibility timeout 10 min, `maxReceiveCount` 3) with dead-letter queue `github-analysis-dlq`. Poison messages (malformed JSON, unsupported `schemaVersion`, missing required field, unknown `jobId`) are not processed and no failure event is sent; they reach the DLQ, and the Core DLQ listener marks the task failed with `RETRIES_EXHAUSTED`. Workers extend visibility while they are still making progress.

## 8. Architectural Notes

- The GitHub Analysis Service is independently deployable.
- The service is implemented in Python.
- Processing is asynchronous and event-driven through Amazon SQS Standard.
- The service retrieves public GitHub repository information through the GitHub API.
- Repository metadata, directory structures, file names and README documentation form the initial analysis scope.
- Full source code analysis is not required for the initial implementation.
- Repositories are not cloned or executed during the Happy Flow.
- The service uses read-only GitHub access through one server-side token from the secret manager.
- AI-based extraction may be used to interpret README documentation and structure project information.
- The analyzer must not present unsupported assumptions as verified technical skills or project features.
- The service does not directly modify the Core Backend PostgreSQL database.
- Analysis results are stored in private S3 storage and referenced through SQS completion messages.
- SQS consumers must support idempotent processing because duplicate deliveries are possible.
- Retrieved README content is treated as untrusted data, including when passed to an AI model.
- The extraction schema is `GitHubAnalysisResult` (Shared Data Contracts §7, `schemaVersion: 1`).

---

## 9. Future Enhancement — Agent-Based Repository Analysis

**Priority:** Very Nice to Have  
**MVP Requirement:** No  
**Included in Happy Flow:** No

A future enhancement could introduce an AI agent operating inside an isolated virtual machine or sandboxed execution environment.

Instead of analyzing only repository metadata and README documentation, the agent could clone selected repositories and inspect the source code in greater detail.

**Potential Capabilities:**

- Clone selected GitHub repositories into an isolated workspace.
- Explore source code and project architecture.
- Identify actual framework and library usage.
- Analyze relationships between application components.
- Identify architectural patterns and implementation approaches.
- Generate more detailed project descriptions supported by code evidence.
- Produce a richer technical profile for the portfolio website.

**Security Considerations:**

- Repositories must be treated as untrusted input.
- Repository content must not execute automatically.
- Analysis must run in an isolated environment with restricted permissions and resource limits.
- Network access and credentials must be tightly controlled.
- Repository access must respect the user's granted permissions.

This enhancement is not a dependency of the initial GitHub Analysis Service.

The MVP must remain fully functional using only GitHub API data and README-based analysis.
