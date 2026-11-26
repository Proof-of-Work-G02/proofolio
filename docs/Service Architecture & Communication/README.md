# Service Architecture & Communication

## 1. Overview

The application follows a modular, event-driven architecture designed to generate and publish personalized portfolio websites using information extracted from CVs, GitHub repositories, and LinkedIn profiles.

The system consists of **5 independently deployable services** plus a small **render worker**, communicating through synchronous HTTP requests and asynchronous message-based events.

The architecture is designed to support parallel development across the Backend, AI, and Frontend teams.

## 2. Service Overview

| Service | Primary Responsibility | Communication |
| --- | --- | --- |
| **Core Backend Service** | Authentication and sessions, ingestion, job orchestration, profile aggregation and frontend APIs | REST, SQS, PostgreSQL, S3 |
| **CV Extraction Service** | Extract structured information from uploaded CVs | SQS, S3 |
| **GitHub Analysis Service** | Analyze public repositories and extract project information and technical evidence, using one server-side GitHub token | SQS, S3, GitHub API |
| **LinkedIn Extraction Service** | Extract structured professional information from user-provided LinkedIn PDF exports | SQS, S3 |
| **Website Service** | Generate, preview and asynchronously publish personalized websites; "my sites" list | SQS, REST, PostgreSQL, S3, AI Provider, render worker |
| **Render worker** | Render an approved draft and its template into static HTML/CSS (Node, AWS Lambda container image) | HTTPS (HMAC-signed), called only by the Website Publisher |

## 3. Service Structure

### Core Backend Service

Contains four internal modules:

- **Authentication Module** — Google and GitHub OAuth, user management and server-side sessions (httpOnly, host-only `pf_session` cookie).
- **Ingestion Module** — Source validation, CV uploads and data ingestion.
- **Job Orchestration Module** — Job creation, retry, task distribution (through a transactional outbox) and processing status tracking.
- **Profile Aggregation Module** — Consolidation of extracted information into a unified user profile.

These modules are part of the same deployable service and communicate internally.

### AI Processing Services

Three independent Python services:

- CV Extraction Service
- GitHub Analysis Service
- LinkedIn Extraction Service

Each service processes a specific data source and reports its results asynchronously. An optional source (GitHub or LinkedIn) that fails does not fail the job; Core records a warning and continues from the CV.

### Website Service

Contains two internal modules:

- **Website Generator** — Generates website drafts using profile data, versioned templates and an AI provider.
- **Website Publisher** — Consumes `website.publish.requested`, calls the render worker, uploads the static files to Amazon S3 and manages publishing metadata.

Both modules belong to the same logical and deployable service.

### Render worker

A small Node service packaged as an AWS Lambda container image. It renders static files from a draft and a template package. It has no database access and accepts only HMAC-signed calls from the Website Publisher.

## 4. Inter-Service Communication

The system uses two primary communication patterns.

### Synchronous Communication — HTTP REST

Used for user-initiated operations requiring a direct API response.

Examples:

- Frontend → Core Backend: Authentication and source submission.
- Frontend → Core Backend: Job status polling, website information and the "my sites" list.
- Core Backend → Website Service: Preview retrieval and publishing requests. Publishing returns `202 Accepted`; the work continues asynchronously.

### Asynchronous Communication — Amazon SQS

Used for long-running AI processing, website generation and website publishing.

Main events:

| Event | Queue | Producer | Consumer |
| --- | --- | --- | --- |
| `cv.extract.requested` | `cv-extraction` | Core Backend | CV Extraction Service |
| `github.analyze.requested` | `github-analysis` | Core Backend | GitHub Analysis Service |
| `linkedin.extract.requested` | `linkedin-extraction` | Core Backend | LinkedIn Extraction Service |
| `processing.completed` / `processing.failed` | `processing-results` | AI Services | Core Backend / Job Orchestrator |
| `profile.ready` | `website-generation` | Core Backend / Profile Aggregator | Website Service (Generator) |
| `website.generated` | `processing-results` | Website Service | Core Backend |
| `website.publish.requested` | `website-publishing` | Website Service (API, through its outbox) | Website Service (Publisher) |
| `website.published` / `website.failed` | `processing-results` | Website Service | Core Backend |

There are six queues, each with its own dead-letter queue. All processing-related messages are correlated using a unique `jobId`.

The exact message schemas, delivery guarantees and error-handling strategies are in SQS Event Contracts, Shared Data Contracts and the Communication Contracts page.

## 5. Data Storage & Infrastructure

| Technology | Purpose |
| --- | --- |
| **PostgreSQL + JSONB** | Users, sessions, jobs, extraction result references, unified profiles, website metadata and drafts, outbox rows |
| **Amazon S3** | Uploaded CVs, extraction results, and published files |
| **Amazon SQS** | Asynchronous task distribution and event communication (six queues, six DLQs) |
| **AWS Lambda (container image)** | Render worker |
| **Amazon CloudFront** | Delivery of published portfolio websites |
| **External AI Provider** | Content extraction, analysis and website content generation (Claude API behind an `LLMClient` interface) |

Each service or module is responsible for its own data domain.

The Core Backend and Website Service use PostgreSQL, with clearly defined ownership of their respective tables.

## 6. Service Documentation

Each service is documented separately using a consistent structure:

1. Purpose
2. Internal Modules
3. Incoming Communication
4. Outgoing Communication
5. Data Ownership
6. Events & API Endpoints
7. Happy Flow
8. Architectural Notes

**Service documentation pages:**

- Core Backend Service
- CV Extraction Service
- GitHub Analysis Service
- LinkedIn Extraction Service
- Website Service
