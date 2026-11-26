# System Architecture – Happy Flow (v1.1)

**Project:** AI-Powered Personal Website Generator  
**Last Updated:** November 26, 2026

---

## 1. Project Overview

The goal of this project is to build an AI-powered platform that automatically generates and hosts personal portfolio websites using information from multiple sources.

Users authenticate through Google or GitHub, provide their CV and optionally their GitHub and LinkedIn profiles, and select a website template.

The platform extracts and consolidates relevant information, generates a personalized website using AI, and allows the user to preview and publish it.

Each published website is accessible through a unique URL, such as:

`https://username.ourdomain.com`

The architecture follows a modular, event-driven approach, enabling independent development of AI processing components and asynchronous execution of long-running tasks.

## 2. High-Level Architecture
![High Level Architecture Diagram](High%20Level%20Architecture%20Diagram.png)

*Note: this diagram is not fully up to date. It does not show the render worker (Lambda) or the `website-publishing` queue. The text below describes the current design.*

The system is organized into the following main components:

| Component | Responsibility |
| --- | --- |
| Frontend | Authentication UI, source submission, template selection, website preview and publishing |
| Core Backend Service | Authentication, ingestion, profile aggregation, job orchestration and application APIs |
| Amazon SQS Standard | Asynchronous communication and task distribution |
| CV Extractor | Extract structured information from uploaded CVs |
| GitHub Analyzer | Analyze GitHub repositories and identify technical skills and projects |
| LinkedIn Extractor | Process available LinkedIn profile information |
| Website Service | Generate, preview and publish personal websites |
| PostgreSQL | Store application data, job statuses, profiles and website metadata |
| Amazon S3 | Store uploaded files and generated website assets |
| Amazon CloudFront | Deliver published websites through public URLs |

## 3. Happy Flow

### Step 1 — User Authentication

The user accesses the application and authenticates using Google or GitHub OAuth.

The Authentication Module within the Core Backend Service validates the user's identity, creates or retrieves the corresponding user record in PostgreSQL and creates a server-side session. The session id is returned in an httpOnly, host-only `pf_session` cookie. OAuth tokens are not stored.

After successful authentication, the user can access the application and initiate the portfolio generation process.

### Step 2 — Source Submission

The user provides the available data sources:

- **CV document** — Uploaded as a file.
- **GitHub profile (optional)** — GitHub username or profile URL.
- **LinkedIn profile (optional)** — User-exported LinkedIn profile PDF.
- **Website template** — The selected template identifier.

The Frontend submits the information to the Core Backend Service through an authenticated HTTP request.

For file uploads, the initial implementation uses `multipart/form-data`.

GitHub information is retrieved through the GitHub REST API using one server-side GitHub token, never a user token. The implementation focuses on public repository metadata, directory structures, file names and README documentation. If GitHub or LinkedIn processing fails, the job continues from the CV and the user sees a warning.

LinkedIn information is obtained from documents explicitly exported and uploaded by the user. Automated LinkedIn scraping is not part of the MVP.

### Step 3 — Data Ingestion

The Ingestion Module, within the Core Backend Service:

1. Validates the incoming request and uploaded files.
2. Stores uploaded CV and LinkedIn documents in private Amazon S3 storage.
3. Validates the provided GitHub username or profile URL.
4. Prepares references to the submitted data sources.
5. Passes the validated information to the Job Orchestration Module.

The Job Orchestration Module:

1. Creates a processing job in PostgreSQL.
2. Creates individual processing tasks for the provided data sources.
3. Assigns a unique `jobId` and task identifiers.
4. Writes the processing requests to an outbox in the same transaction; a relay sends them to the corresponding Amazon SQS Standard queues.

**Message Queue Distribution:**

| Queue | Event | Consumer |
| --- | --- | --- |
| `cv-extraction` | `cv.extract.requested` | CV Extraction Service |
| `github-analysis` | `github.analyze.requested` | GitHub Analysis Service |
| `linkedin-extraction` | `linkedin.extract.requested` | LinkedIn Extraction Service |

Only services corresponding to the provided sources are invoked.

The Core Backend Service returns the unique `jobId` to the Frontend, allowing the user to track processing progress.

### Step 4 — AI Processing

Three independent AI Processing Services handle source-specific processing.

Each service consumes messages from its dedicated Amazon SQS queue.

**CV Extraction Service**

1. Consumes a `cv.extract.requested` message from the `cv-extraction` queue.
2. Retrieves the uploaded CV from private Amazon S3 storage.
3. Extracts the document's textual content.
4. Identifies relevant professional information, including education, work experience, skills and projects.
5. Converts the extracted information into structured JSON.
6. Stores the extraction result in private Amazon S3 storage.

**GitHub Analysis Service**

1. Consumes a `github.analyze.requested` message from the `github-analysis` queue.
2. Connects to GitHub using the GitHub REST API.
3. Retrieves the user's public repositories and relevant metadata.
4. Retrieves repository directory structures and file names.
5. Retrieves and analyzes README documentation.
6. Identifies technologies, project descriptions and documented features.
7. Produces structured JSON containing the extracted project information.
8. Stores the analysis result in private Amazon S3 storage.

The initial implementation does not require repository cloning, source code execution or autonomous repository analysis agents.

**LinkedIn Extraction Service**

1. Consumes a `linkedin.extract.requested` message from the `linkedin-extraction` queue.
2. Retrieves the user-exported LinkedIn PDF from private Amazon S3 storage.
3. Extracts the document's textual content.
4. Identifies professional experience, education, skills and other relevant information.
5. Converts the extracted information into structured JSON.
6. Stores the extraction result in private Amazon S3 storage.

**Processing Completion**

After successfully completing its task, each AI Processing Service sends a `processing.completed` message to the Amazon SQS `processing-results` queue.

The message contains the identifiers required to associate the result with its original job and task, together with a reference to the stored extraction result.

Large extraction results and original documents are not included directly in SQS messages.

### Step 5 — Job Orchestration

The Job Orchestration Module consumes `processing.completed` messages from the Amazon SQS `processing-results` queue.

For each completed task, the module:

1. Identifies the processing job and task using their identifiers.
2. Retrieves the extraction result from private Amazon S3 storage.
3. Records the result or its storage reference in PostgreSQL.
4. Updates the corresponding task status.
5. Determines whether all requested processing tasks have completed.

Only tasks corresponding to the user's submitted sources are required.

For example, if the user provides only a CV and GitHub profile, the Job Orchestration Module waits for those two processing tasks without requiring LinkedIn extraction.

Once every requested task is finished and the CV task completed, the Job Orchestration Module triggers the Profile Aggregation Module **internally**. A failed optional source (GitHub or LinkedIn) is left out and recorded as a job warning; a failed CV task fails the job.

No additional SQS message is required between these modules because both belong to the same Core Backend Service.

### Step 6 — Profile Aggregation

The Profile Aggregation Module, within the Core Backend Service, retrieves the completed extraction results.

Its responsibilities include:

- Combining information from CV, GitHub and LinkedIn sources.
- Eliminating duplicated information.
- Reconciling overlapping or conflicting information.
- Normalizing technical skills, professional experience, education and project descriptions.
- Preserving supporting evidence and source references where available.
- Producing a unified user profile.

The unified profile is stored in PostgreSQL using JSONB.

After successful aggregation, the Profile Aggregation Module sends a `profile.ready` message to the Amazon SQS Standard `website-generation` queue.

The event provides the identifiers required by the Website Service to retrieve the unified profile and selected template.

### Step 7 — Website Generation

The Website Generator Module, within the Website Service, consumes the `profile.ready` message from the Amazon SQS `website-generation` queue.

The module:

1. Retrieves the unified user profile from PostgreSQL.
2. Retrieves the selected website template.
3. Calls an external AI provider to generate or adapt personalized website content.
4. Produces a website draft compatible with the selected template.
5. Stores the generated draft and associated website metadata in PostgreSQL.
6. Updates the website generation status.
7. Sends a `website.generated` message to the Amazon SQS `processing-results` queue.

The Core Backend Service consumes the `website.generated` message and updates the corresponding job status.

The generated website is now available for user preview.

### Step 8 — Website Preview

The Frontend retrieves the generated website through the Core Backend API.

The Core Backend Service validates the user's authorization and communicates with the Website Service through HTTP REST.

**Internal Endpoint:**

`GET /internal/websites/{websiteId}/preview`

The Website Service retrieves the generated draft from PostgreSQL and returns the information required to display the preview.

The Frontend displays the generated website, allowing the user to review its content and visual appearance.

The website remains unpublished during this stage and does not require a public subdomain.

### Step 9 — Website Publishing

When the user approves the generated website, they select a preferred subdomain and choose **Publish**.

**Example:**

`stefan-dobrincu.ourdomain.com`

The Frontend sends the publishing request to the Core Backend API, including the selected slug.

The Core Backend Service validates the user's identity and website ownership, then forwards the authorized request to the Website Service. Publishing is asynchronous: the request returns `202 Accepted` and the frontend polls the job status.

**Internal Endpoint:**

`POST /internal/websites/{websiteId}/publish`

The Website Service, on the publish request:

1. Retrieves the approved website draft from PostgreSQL.
2. Receives the user-selected subdomain slug.
3. Validates the slug format and checks reserved subdomain names.
4. Rejects the request with `409 SLUG_TAKEN` if another user owns the slug. If the same user republishes, the older website with that slug becomes `UNPUBLISHED`. Slugs cannot be renamed after the first publish.
5. In one transaction moves the website to `PUBLISHING`, reserves the slug (enforced by a `UNIQUE` constraint) and writes a `website.publish.requested` outbox row, then returns `202 Accepted`.

The Website Publisher Module then:

1. Consumes the event from the `website-publishing` queue.
2. Calls the render worker (Node, AWS Lambda container image, HMAC-authenticated) to render the static HTML and CSS.
3. Uploads the static files to Amazon S3 under the slug prefix, with `index.html` last.
4. Updates the website status, S3 location and public URL in PostgreSQL.
5. Sends `website.published` to the Amazon SQS `processing-results` queue. On failure it sends `website.failed` with `stage = WEBSITE_PUBLISHING`; the website becomes `PUBLISH_FAILED` and the job returns to `PREVIEW_READY` so the user can try again.

The Core Backend Service consumes the result event and makes the published website URL available to the Frontend, which learns it by polling the job status. Published sites are also listed under "My sites" (`GET /api/websites`).

**Subdomain Uniqueness**

Each published website must have a globally unique subdomain.

The slug is independent of the user's display name.

Two users with the same name can publish separate websites using different slugs.

Examples:

- `alex-popescu.ourdomain.com`
- `alex-popescu-dev.ourdomain.com`

PostgreSQL enforces slug uniqueness to prevent conflicts, including simultaneous publishing requests.

### Step 10 — Website Hosting

Published websites are served using Amazon S3 and Amazon CloudFront.

Each website is accessible through its unique user subdomain.

**Example:**

`https://stefan-dobrincu.ourdomain.com`

The hosting infrastructure uses:

- **Amazon S3** — Stores published static website files.
- **Amazon CloudFront** — Delivers websites through HTTPS and caches static assets.
- **Wildcard DNS** — Routes user subdomains to the shared CloudFront distribution.
- **Wildcard TLS Certificate** — Provides HTTPS for user subdomains.
- **CloudFront Function** — Identifies the requested subdomain and rewrites the URI to the appropriate S3 object.

All published websites share the same S3 bucket and CloudFront distribution.

**Example S3 Structure:**

```
published-websites/
  stefan-dobrincu/
    index.html
    assets/
      style.css
      script.js
      profile.webp

  alex-popescu/
    index.html
    assets/
      style.css
      script.js
      profile.webp
```

**Example Routing:**

Incoming request:

```
https://stefan-dobrincu.ourdomain.com
```

CloudFront Function identifies the subdomain and rewrites the request to:

```
/stefan-dobrincu/index.html
```

Static asset requests are similarly mapped to the corresponding website prefix.

The routing configuration must prevent requests from accessing another website's files through path manipulation.

The published S3 origin remains private and is accessed through CloudFront.

The platform does not require a separate S3 bucket, CloudFront distribution, application server or container for every published website.

Once published, portfolio websites are served as static assets without invoking the Website Service or the external AI provider.

---

**Happy Flow Summary**

The complete processing flow is:

1. User authentication through Google or GitHub OAuth.
2. CV upload, optional GitHub/LinkedIn data submission and template selection.
3. Source ingestion and processing job creation.
4. Asynchronous AI processing through dedicated Amazon SQS queues.
5. Processing result delivery through Amazon S3 and the shared SQS results queue.
6. Internal profile aggregation within the Core Backend Service.
7. Asynchronous website generation triggered by `profile.ready`.
8. Website preview through the Core Backend API.
9. User-approved publication with a unique subdomain.
10. Static website hosting through Amazon S3 and CloudFront.

**Messaging Technology:** Amazon SQS Standard (AWS), ElasticMQ (local development).

**Object Storage:** Amazon S3 (AWS), RustFS (local development).

**Database:** PostgreSQL (Amazon RDS in AWS, Docker locally).

**Deployment Infrastructure:** Terraform for AWS, Docker Compose for local development.

**Contract Status:** Detailed HTTP, SQS and shared data contracts are in the HTTP API Contracts, SQS Event Contracts, Shared Data Contracts and Communication Standards documents. Failure handling is in the Failure Handling Design.

## 4. Backend Architecture

The Core Backend Service is a single deployable microservice organized into four internal modules: Authentication, Ingestion, Job Orchestration and Profile Aggregation.

| Module | Responsibilities |
| --- | --- |
| Auth Module | OAuth authentication, user management and session handling |
| Ingestor Module | Request validation, source ingestion and S3 uploads |
| Job Orchestrator | Job creation, task dispatching, status tracking and aggregation triggering |
| Profile Aggregation | Combine extraction results and create unified profiles |

The modules share a backend application but maintain separate responsibilities.

This approach minimizes deployment overhead while allowing individual modules to evolve independently.

## 5. Website Service

The Website Service is responsible for generating, previewing and publishing personalized portfolio websites based on the user's unified profile and selected template.

It is a single independently deployable microservice containing two internal modules:

- **Website Generator**
- **Website Publisher**

Both modules belong to the same service but have separate responsibilities.

### 5.1 Website Generator

The Website Generator is responsible for transforming a unified user profile into a personalized website draft.

**Responsibilities:**

- Consume `profile.ready` messages from the Amazon SQS `website-generation` queue.
- Retrieve the unified user profile from PostgreSQL.
- Retrieve the selected website template.
- Integrate with an external AI provider to generate or adapt website content.
- Generate a website draft compatible with the selected template.
- Store the generated website draft and associated metadata in PostgreSQL.
- Publish a `website.generated` message to the Amazon SQS `processing-results` queue.

The generated website remains unpublished until explicitly approved by the user.

The Frontend retrieves the generated draft through the Core Backend Service using HTTP REST communication.

### 5.2 Website Publisher

The Website Publisher is responsible for publishing approved website drafts under unique user subdomains.

**Responsibilities:**

- Receive authorized publishing requests from the Core Backend Service through HTTP REST and return `202 Accepted`.
- Retrieve the approved website draft from PostgreSQL.
- Receive and validate the user's selected subdomain slug.
- Verify that the requested slug is not reserved or already in use.
- Atomically reserve the unique slug in PostgreSQL.
- Reject conflicting publishing requests with `409 Conflict`.
- Validate and prepare static HTML, CSS, JavaScript and other website assets.
- Upload the static website files to Amazon S3.
- Update website publishing metadata and status in PostgreSQL.
- Consume `website.publish.requested` from the `website-publishing` queue, render through the render worker and publish `website.published` or `website.failed` to the `processing-results` queue.
- Make the published website URL available to the Core Backend Service through the result event.

**Subdomain Example:**

`https://stefan-dobrincu.ourdomain.com`

Each published website has a globally unique subdomain identifier.

The subdomain is independent of the user's display name, allowing users with identical names to publish different websites.

Slug uniqueness is enforced through a PostgreSQL `UNIQUE` constraint.

### 5.3 Website Hosting

Published websites are hosted as static files using Amazon S3 and Amazon CloudFront.

The infrastructure includes:

- **Amazon S3:** Storage for published website files.
- **Amazon CloudFront:** HTTPS delivery and caching.
- **Wildcard DNS:** Routing for `*.ourdomain.com`.
- **Wildcard TLS Certificate:** HTTPS support for user subdomains.
- **CloudFront Function:** Hostname-based URI rewriting.

All published websites share one S3 bucket and one CloudFront distribution.

Each website is stored under a separate prefix corresponding to its unique slug.

**Example S3 Structure:**

```
published-websites/
  stefan-dobrincu/
    index.html
    assets/
      style.css
      script.js

  maria-popescu/
    index.html
    assets/
      style.css
      script.js
```

When a visitor accesses:

`https://stefan-dobrincu.ourdomain.com`

CloudFront identifies the subdomain and internally routes the request to the corresponding website files in Amazon S3.

The routing configuration must prevent users from accessing another website's files through URI manipulation.

Once published, websites are served directly through CloudFront without invoking the Website Service or an external AI provider.

**Architectural Principles:**

- Website generation and publishing are separate operations.
- Website generation is asynchronous and event-driven.
- Preview and publish requests use HTTP REST through the Core Backend Service; publishing is asynchronous.
- Publishing requires explicit user approval.
- Each published website has a globally unique subdomain.
- A separate application server, S3 bucket or CloudFront distribution is not required for each website.

## 6. Data Persistence

PostgreSQL is the primary relational database.

JSONB columns are used where flexible structures are required, particularly for AI extraction results and unified user profiles.

### Database Tables

| Table | Purpose | Primary Owner |
| --- | --- | --- |
| `users` | Application users | Auth Module |
| `oauth_accounts` | External authentication identities | Auth Module |
| `sessions` | Server-side login sessions | Auth Module |
| `jobs` | Processing jobs and overall status | Job Orchestration Module |
| `job_tasks` | Individual AI task status | Job Orchestration Module |
| `extraction_results` | References (and an optional copy) of AI results stored in S3 | Job Orchestration Module |
| `profiles` | Unified personal profiles | Profile Aggregator Module |
| `websites` | Website ownership, unique slug, draft and publishing state | Website Service |
| `outbox` | Events waiting to be published (one per service) | Core Backend / Website Service |
| `dlq_seen` | Dead-letter messages already handled | Core Backend |

Each module is responsible for the data it owns.

The Job Orchestrator, Profile Aggregator, Website Service and Auth Module interact with PostgreSQL according to their responsibilities.

Large files and static website assets are stored in Amazon S3 rather than directly in PostgreSQL.

## 7. Event-Driven Communication

The application uses asynchronous, message-based communication to coordinate AI processing and website generation.

**Selected Technology:** Amazon Simple Queue Service (Amazon SQS) Standard

Amazon SQS decouples services and allows long-running processing tasks to execute without blocking HTTP requests.

Each AI Processing Service consumes messages from its dedicated queue, while processing completion events are delivered to a shared results queue.

### 7.1 Messaging Infrastructure

The application uses six queues, each with its own dead-letter queue.

| Queue | Purpose |
| --- | --- |
| `cv-extraction` | Distribute CV extraction tasks |
| `github-analysis` | Distribute GitHub analysis tasks |
| `linkedin-extraction` | Distribute LinkedIn extraction tasks |
| `processing-results` | Deliver AI processing and website completion events to Core Backend |
| `website-generation` | Trigger website generation after profile aggregation |
| `website-publishing` | Trigger asynchronous website publishing |

All queues use Amazon SQS Standard in the AWS environment.

During local development, ElasticMQ provides an SQS-compatible implementation.

Both environments use the AWS SDK, with environment-specific queue URLs and endpoint configuration.

### 7.2 Events

The system defines ten event types.

| Event | Queue | Producer | Consumer |
| --- | --- | --- | --- |
| `cv.extract.requested` | `cv-extraction` | Job Orchestrator | CV Extraction Service |
| `github.analyze.requested` | `github-analysis` | Job Orchestrator | GitHub Analysis Service |
| `linkedin.extract.requested` | `linkedin-extraction` | Job Orchestrator | LinkedIn Extraction Service |
| `processing.completed` | `processing-results` | AI Processing Services | Core Backend / Job Orchestrator |
| `processing.failed` | `processing-results` | AI Processing Services | Core Backend / Job Orchestrator |
| `profile.ready` | `website-generation` | Core Backend / Profile Aggregator | Website Service (Generator) |
| `website.generated` | `processing-results` | Website Service | Core Backend / Job Orchestrator |
| `website.publish.requested` | `website-publishing` | Website Service (API, through its outbox) | Website Service (Publisher) |
| `website.published` | `processing-results` | Website Service (Publisher) | Core Backend |
| `website.failed` | `processing-results` | Website Service | Core Backend / Job Orchestrator |

### 7.3 Processing Request Flow

After receiving and validating the user's submitted data sources, the Job Orchestration Module creates a processing job and the corresponding processing tasks.

Each task is dispatched to its dedicated Amazon SQS queue.

- CV extraction requests are sent to `cv-extraction`.
- GitHub analysis requests are sent to `github-analysis`.
- LinkedIn extraction requests are sent to `linkedin-extraction`.

Only the services corresponding to the user's provided sources are invoked.

Processing tasks execute independently and can run concurrently.

### 7.4 Processing Result Flow

After completing their assigned tasks, the AI Processing Services store their structured extraction results in private Amazon S3 storage.

Each service then publishes a `processing.completed` message to the `processing-results` queue.

The completion messages contain:

- Processing job identifier.
- Processing task identifier.
- Source type.
- Processing status.
- Reference to the stored extraction result.

The Core Backend Service consumes the completion messages and updates the corresponding processing task statuses in PostgreSQL.

When all requested tasks have completed successfully, the Job Orchestration Module triggers the Profile Aggregation Module internally.

**No **`aggregation.requested`** event is required**, because the Job Orchestration Module and Profile Aggregation Module are part of the same deployable Core Backend Service.

### 7.5 Website Generation Events

After the unified profile has been created and stored in PostgreSQL, the Profile Aggregation Module sends a `profile.ready` message to the `website-generation` queue.

The Website Service consumes this message and begins generating the personalized website.

Once generation completes successfully, the Website Service publishes `website.generated` to the `processing-results` queue.

The Core Backend Service consumes the event and makes the generated website available for frontend preview.

After explicit user approval, the publish request returns `202` and the Website Service queues `website.publish.requested` to the `website-publishing` queue. The Website Publisher consumes it and, on success, sends `website.published` to the `processing-results` queue; on failure it sends `website.failed` and the job returns to `PREVIEW_READY`.

### 7.6 Messaging Principles

**Message Correlation**

Messages use `jobId` and `taskId`, where applicable, to associate processing events with the corresponding jobs and tasks.

The exact event metadata and payload schemas will be defined in the Event Contracts documentation.

**Message Delivery**

Amazon SQS Standard provides at-least-once message delivery and does not guarantee strict message ordering.

Consumers must implement idempotent processing to prevent duplicated operations.

**Large Payload Handling**

Original documents and large extraction results are stored in Amazon S3 rather than included directly in SQS messages.

Messages carry identifiers and storage references.

**Queue Ownership**

Each queue has clearly defined producers and consumers.

The `processing-results` queue is consumed by the Core Backend Service, which processes messages according to their event types.

**Local Compatibility**

ElasticMQ provides an SQS-compatible interface for local development and integration testing.

AWS-specific behavior, including Lambda event source mappings and production message delivery semantics, must also be verified through integration testing in AWS.

**Contract Definition**

Detailed event payloads, data types, validation rules, retry behavior and message processing requirements will be documented separately.

## 8. Technology Stack

The application uses a microservices-based architecture with separate local development and AWS deployment environments.

The local environment supports development, automated testing and service integration without requiring active AWS infrastructure.

The AWS environment is used for deployment, integration verification and demonstrations.

### 8.1 Application Technologies

| Layer | Technology / Approach |
| --- | --- |
| Frontend | React-based web application |
| Core Backend | Modular backend HTTP API |
| AI Processing | Independent Python microservices |
| Website Service | Website Generator and Website Publisher modules |
| AI Integration | External LLM provider |
| Authentication | Google / GitHub OAuth (custom, server-side sessions) |
| Database | PostgreSQL + JSONB |
| Asynchronous Communication | Amazon SQS-compatible messaging |
| Object Storage | S3-compatible object storage |
| Published Website Format | Static HTML, CSS, JavaScript and assets |
| Version Control | Git / GitHub |
| CI/CD | GitHub Actions |

### 8.2 Environment Infrastructure

| Component | Local Development | AWS Deployment |
| --- | --- | --- |
| Service Execution | Docker Compose | AWS Lambda container image for the render worker; the other services run on ECS Fargate |
| Database | PostgreSQL Docker | Amazon RDS PostgreSQL |
| Message Queue | ElasticMQ | Amazon SQS Standard |
| Object Storage | RustFS | Amazon S3 |
| Frontend | Local development server | AWS hosting configuration — TBD |
| Published Websites | Local static hosting / testing | Amazon S3 + CloudFront |
| Subdomain Routing | Local routing simulation | Wildcard DNS + CloudFront Function |
| TLS | Local configuration as required | Wildcard certificate through AWS Certificate Manager |
| Infrastructure Provisioning | Docker Compose | Terraform |
| CI/CD | GitHub Actions | GitHub Actions |
| Monitoring | Local logs | Amazon CloudWatch |

### 8.3 Local Development Environment

The local development environment uses Docker Compose to run the required services and supporting infrastructure.

The environment includes:

- Core Backend Service.
- CV Extraction Service.
- GitHub Analysis Service.
- LinkedIn Extraction Service.
- Website Service.
- PostgreSQL.
- ElasticMQ.
- RustFS.

Services communicate using the same logical API and event contracts as the AWS environment.

ElasticMQ provides an SQS-compatible API, while RustFS provides an S3-compatible object storage API. RustFS replaces MinIO, which stopped publishing Docker images in 2025; both speak the same S3 API.

The application uses environment-specific configuration to connect to local or AWS infrastructure.

The local environment is used for:

- Daily development.
- Unit testing.
- Integration testing.
- Contract testing.
- End-to-end Happy Flow verification.

### 8.4 AWS Deployment Environment

The AWS environment is provisioned using Terraform.

The proposed infrastructure includes:

- **AWS Lambda:** The Node render worker, packaged as a container image. **ECS Fargate:** The other services.
- **Amazon RDS PostgreSQL:** Relational data storage.
- **Amazon SQS Standard:** Asynchronous communication between services.
- **Amazon S3:** Private document storage, extraction results and published website files.
- **Amazon CloudFront:** Public delivery of generated websites.
- **AWS Certificate Manager:** TLS certificates for published website subdomains.
- **CloudFront Functions:** Hostname-based routing for published websites.
- **AWS IAM:** Service permissions and access control.
- **Amazon CloudWatch:** Application logs and infrastructure monitoring.

Detailed deployment topology is defined in the Infrastructure Design.

The system is designed to support lightweight, event-driven workloads through AWS Lambda and workloads requiring additional resources or longer execution times through ECS Fargate.

### 8.5 Deployment Strategy

The project follows a local-first development approach.

Most development and automated testing take place locally.

AWS infrastructure is primarily used for:

- Validating real AWS service integrations.
- Testing the complete deployed Happy Flow.
- Verifying Terraform infrastructure configuration.
- Running demonstrations.

Terraform enables reproducible infrastructure provisioning.

AWS resources may be provisioned for testing and removed when no longer required, reducing unnecessary cloud costs.

**Architectural Principle:**

Local and AWS environments must preserve the same logical service boundaries, API contracts, event contracts and data structures.

Infrastructure-specific differences must remain isolated from application business logic.

## 9. Key Architecture Decisions

### ADR-001 — Independent AI Processing Services

Each data source is processed by a dedicated, independently deployable AI service.

The system includes:

- CV Extraction Service
- GitHub Analysis Service
- LinkedIn Extraction Service

This separation enables independent implementation, deployment and testing.

Each service has a clearly defined responsibility and communicates with the Core Backend Service asynchronously.

### ADR-002 — Asynchronous Processing with Amazon SQS

Amazon SQS Standard is selected for asynchronous communication between services.

Long-running AI extraction and website generation operations are executed independently from HTTP requests.

Dedicated queues are used for processing, generation and publishing requests, while a shared results queue handles completion and failure events. Each queue has a dead-letter queue.

ElasticMQ provides an SQS-compatible alternative for local development.

All consumers must implement idempotent message processing.

### ADR-003 — Centralized Job Orchestration

The Job Orchestration Module is responsible for coordinating processing jobs and monitoring individual AI processing tasks.

Only tasks corresponding to the user's submitted sources are created.

Profile aggregation begins when all requested processing tasks have completed successfully.

Job Orchestration and Profile Aggregation are internal modules of the Core Backend Service and do not require asynchronous communication between them.

### ADR-004 — PostgreSQL as Primary Database

PostgreSQL is selected as the primary application database.

Relational structures are used for users, authentication identities, jobs, processing tasks and website metadata.

JSONB is used for flexible, structured information such as AI extraction results and unified user profiles.

The Core Backend Service and Website Service have clearly defined data ownership responsibilities.

### ADR-005 — Unified Website Service

Website generation and publishing are implemented within one independently deployable Website Service.

The service contains two internal modules:

- Website Generator
- Website Publisher

Website generation and publishing are initiated asynchronously through SQS. Preview and publish requests are accessed through HTTP REST with the Core Backend Service, and publishing returns `202 Accepted`. The static rendering runs in a separate render worker (a Node Lambda container image).

Publishing requires explicit user approval.

### ADR-006 — Static Website Hosting

Generated portfolio websites are published as static HTML, CSS, JavaScript and associated assets.

Published files are stored in Amazon S3 and delivered through Amazon CloudFront.

This approach eliminates the need to run a dedicated application server or container for every published portfolio website.

### ADR-007 — Unique User Subdomains

Each published portfolio website is accessible through a globally unique user subdomain.

**Example:** `https://username.ourdomain.com`

The Website Publisher validates and reserves the selected slug during publication.

PostgreSQL enforces slug uniqueness through a database constraint.

Published websites share a single S3 bucket and CloudFront distribution.

Wildcard DNS and a wildcard TLS certificate support user subdomains, while a CloudFront Function performs hostname-based URI rewriting.

### ADR-008 — GitHub REST API for Initial Analysis

The GitHub Analysis Service uses the GitHub REST API with a server-side GitHub token for the initial implementation. No user GitHub token is stored or passed in events.

Analysis focuses on:

- Public repository metadata.
- Directory structures.
- File and directory names.
- README documentation.
- Project descriptions and technology identification.

Repository cloning and autonomous agent-based source code analysis are excluded from the MVP.

Private repository access may be considered separately after the initial implementation.

### ADR-009 — User-Provided LinkedIn Profile Data

LinkedIn information is obtained through profile documents explicitly exported and uploaded by users.

The LinkedIn Extraction Service processes the uploaded PDF documents and transforms their contents into structured professional information.

Automated LinkedIn scraping is not part of the MVP.

The additional user steps required for profile export are recognized as a user experience limitation.

### ADR-010 — Local-First Development

The application is developed and tested primarily in a local Docker Compose environment.

PostgreSQL, ElasticMQ and RustFS provide local alternatives to managed AWS infrastructure.

Application services use the same logical interfaces in local and AWS environments.

Real AWS integration testing remains necessary to verify cloud-specific behavior.

### ADR-011 — Terraform-Based AWS Infrastructure

Terraform is selected as the Infrastructure as Code solution for AWS resources.

Infrastructure configuration is version-controlled in GitHub.

The AWS environment is used primarily for integration verification and demonstrations, while local infrastructure supports daily development.

The final compute configuration, including the allocation of services to AWS Lambda or ECS Fargate, will be defined during Infrastructure Design.

## 10. Open Questions

The following decisions are not required to finalize the logical Happy Flow, but must be addressed before deployment or during implementation planning.

- **Hosting:** Final sizing of the ECS Fargate services.
- **Authentication:** Custom Google and GitHub OAuth with an httpOnly host-only session cookie is the chosen approach.
- **Preview:** The preview is read-only in v1; editing, profile photos and third-party templates are out of scope.
- **Service Contracts:** API schemas, event payloads and normalized extraction formats.
- **Security:** Access control, private source storage, safe generated content and isolation of published websites.

## 11. Scope of This Document

This document describes the **Happy Flow**: the successful execution path from authentication to publishing a personal website.

The following topics are outside the current scope and will be documented separately:

- Detailed monitoring thresholds.
- Monitoring, logging and observability.
- Detailed deployment topology and infrastructure configuration.
- Database migrations and final database schema.
- Detailed API and message contracts.
- Security threat modeling.

---

**Next Steps:** Agree on service ownership, define API/event contracts, finalize the database schema and create the initial development tasks.
