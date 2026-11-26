# Shared Data Contracts

**Project:** AI-Powered Personal Website Generator  
**Scope:** MVP / Happy Flow  
**Data Format:** JSON  
**Schema Standard:** JSON Schema (Draft 2020-12)

## 1. Purpose

This document defines the shared data structures exchanged and consumed by the application's microservices.

It establishes standardized JSON schemas for source-specific extraction results, unified professional profiles, and generated website drafts.

The objective is to ensure that independently developed services produce and consume compatible data without depending on each other's internal implementations.

The contracts cover:

- CV Extraction Results
- LinkedIn Extraction Results
- GitHub Analysis Results
- Canonical Professional Profile
- Unified User Profile
- Website Draft

These structures are used throughout the portfolio generation workflow, from source extraction to website generation, preview and publishing.

The schemas presented here are v1 contracts. The machine-readable JSON Schemas in the shared `contracts/` directory are authoritative.

---

## 2. Data Exchange Architecture

The application uses three primary data exchange mechanisms.

| Mechanism | Purpose | Data |
| --- | --- | --- |
| Amazon S3 | Store uploaded documents and extraction results | Files and JSON |
| PostgreSQL JSONB | Store unified profiles and generated website drafts | Structured JSON |
| HTTP REST | Return website drafts for frontend preview | JSON |

Amazon SQS coordinates asynchronous processing but does not transport complete extraction results or unified profiles.

Instead, SQS messages contain identifiers and storage references.

### 2.1 Data Flow

The structured data lifecycle follows these steps:

1. The Core Backend stores uploaded CV and LinkedIn documents in private S3 storage.
2. AI Processing Services retrieve their assigned inputs.
3. Each AI Processing Service produces a source-specific structured JSON result.
4. The results are validated and stored in private S3 storage. The S3 object is the source of truth; Core may keep an optional JSONB copy for querying.
5. The Core Backend retrieves the results using references received through SQS.
6. The Profile Aggregation Module combines the available results into a unified profile.
7. The unified profile is stored in PostgreSQL using JSONB.
8. The Website Service reads the unified profile and generates a website draft.
9. The website draft is stored in PostgreSQL.
10. The draft is returned through HTTP REST for frontend preview.
11. After approval, the Website Service publishes the site asynchronously: it renders static files and uploads them to S3.

### 2.2 Data Contract Registry

| Contract | Producer | Consumer | Storage |
| --- | --- | --- | --- |
| `CVExtractionResult` | CV Extraction Service | Core Backend | S3 |
| `LinkedInExtractionResult` | LinkedIn Extraction Service | Core Backend | S3 |
| `GitHubAnalysisResult` | GitHub Analysis Service | Core Backend | S3 |
| `CanonicalProfessionalProfile` | CV / LinkedIn extractors | Profile Aggregator | Embedded JSON |
| `UnifiedProfile` | Profile Aggregator | Website Service | PostgreSQL JSONB |
| `WebsiteDraft` | Website Service | Core Backend / Frontend | PostgreSQL JSONB / HTTP |

Each contract has an authoritative schema that must be followed by its producer and validated by its consumers.

---

## 3. Common Extraction Result Structure

All three AI Processing Services must produce results containing consistent processing metadata.

### 3.1 Common Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| schemaVersion | Integer | Yes | Data contract version |
| jobId | String | Yes | Associated processing job |
| taskId | String | Yes | Associated processing task |
| sourceType | Enum | Yes | Original information source |

**Supported Source Types**

- `CV`
- `GITHUB`
- `LINKEDIN`

### 3.2 Common Result Example

```json
{
  "schemaVersion": 1,
  "jobId": "job-456",
  "taskId": "task-789",
  "sourceType": "CV"
}
```

Each processing service extends these common fields with its source-specific result structure.

**Validation Rules**

- `schemaVersion` must be supported by the consuming service.
- `jobId` must identify an existing processing job.
- `taskId` must identify an existing task belonging to that job.
- `sourceType` must match the type assigned to the processing task.
- The JSON structure must conform to its source-specific schema.

The Core Backend Service validates the relationship between the submitted identifiers and its persisted processing records.

Identifiers are treated as opaque strings. Consumers must not depend on the illustrative prefixes used in documentation examples.

---

### 3.3 Failure Information (`FailureInfo`)

Failure events (`processing.failed`, `website.failed`) and the `error` object returned by the HTTP API use these fields.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| stage | Enum | Yes | `CV_EXTRACTION`, `GITHUB_ANALYSIS`, `LINKEDIN_EXTRACTION`, `WEBSITE_GENERATION`, `WEBSITE_PUBLISHING` |
| errorCode | Enum | Yes | See the error code table below |
| errorMessage | String | Yes | Short and safe to show to a user. No stack traces, CV text, personal data or secrets. |
| retryable | Boolean | Yes | Whether the user can reasonably retry as is |
| attempts | Integer | Yes (events only) | Processing attempts made before giving up |
| diagnosticsS3Key | String | No (events only) | Optional pointer to a log or debug object in a private bucket |

The HTTP `error` object on a failed job is `{ "code", "message", "stage", "retryable" }`, mapped from `errorCode`, `errorMessage`, `stage` and `retryable`.

**Error codes** (starting set; services may add codes but must not repurpose existing ones)

| Code | Group | Typical retryable |
| --- | --- | --- |
| `SOURCE_UNREADABLE` | Permanent | No |
| `SOURCE_NOT_FOUND` (for example, GitHub user) | Permanent | No |
| `SOURCE_EMPTY` (no usable content) | Permanent | No |
| `AI_OUTPUT_INVALID` | Permanent after retries | Yes |
| `AI_PROVIDER_UNAVAILABLE` | Transient, retries exhausted | Yes |
| `EXTERNAL_RATE_LIMITED` | Transient, retries exhausted | Yes |
| `STORAGE_ERROR` | Transient, retries exhausted | Yes |
| `INTERNAL_ERROR` | Either | Yes |
| `TIMEOUT` | Raised by the Core watchdog | Yes |
| `RETRIES_EXHAUSTED` | Raised by the Core DLQ listener | Yes |
| `SLUG_TAKEN`, `PUBLISH_ASSET_ERROR` | Publishing | `SLUG_TAKEN` needs a user change |
| `SLUG_CONFLICT` | HTTP only (a different slug requested for an already published site) | Needs a user change |
| `JOB_NOT_RETRYABLE` | HTTP only (retry of a job that cannot be retried) | No |
| `RATE_LIMITED` | HTTP only (request, upload or generation limits; `429`) | Yes, later |

### 3.4 Job Warnings (`JobWarning`)

A failed **optional** source (GitHub or LinkedIn) does not fail the job. Core Backend records a warning instead, stored in `jobs.warnings` (JSONB array, default `[]`) and returned by `GET /api/jobs/{jobId}`.

```json
{
  "sourceType": "GITHUB",
  "errorCode": "SOURCE_NOT_FOUND",
  "message": "GitHub could not be imported. Your site was built from your CV."
}
```

Warnings do not change a job's status. A job in `PREVIEW_READY` with warnings is a success.

---

## 4. Canonical Professional Profile

CV and LinkedIn documents contain overlapping categories of professional information.

To simplify profile aggregation, both extraction services use a shared professional data structure.

This structure is called `CanonicalProfessionalProfile`.

It defines how personal information, work experience, education, skills, and other professional details are represented.

### 4.1 Profile Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| fullName | String | No | Person's full name |
| headline | String | No | Professional headline |
| location | String | No | Reported location |
| email | String | No | Contact email |
| phone | String | No | Contact telephone number |
| links | Array of strings | No | Professional URLs |
| summary | String | No | Professional summary |
| workExperience | Array of objects | No | Employment history |
| education | Array of objects | No | Academic history |
| skills | Array of strings | No | Technical and professional skills |
| projects | Array of objects | No | Personal or professional projects |
| certifications | Array of objects | No | Certifications and qualifications |
| languages | Array of objects | No | Languages and proficiency |
| volunteering | Array of objects | No | Volunteering experience |
| awards | Array of objects | No | Honors and achievements |

Fields are optional because input documents may contain different amounts of information.

### 4.2 Work Experience

Each work experience entry uses the following structure.

```json
{
  "company": "Example Company",
  "position": "Software Developer Intern",
  "description": "Developed backend APIs using Java.",
  "startDate": "2026-07",
  "endDate": "2026-09",
  "isCurrent": false
}
```

**Fields**

| Field | Type | Description |
| --- | --- | --- |
| company | String | Employer or organization |
| position | String | Job title |
| description | String | Responsibilities and achievements |
| startDate | String | Employment start date |
| endDate | String | Employment end date |
| isCurrent | Boolean | Whether the position is ongoing |

All fields may be omitted when unavailable, subject to the item validation rules in the JSON Schema.

Dates may contain different precision levels:

- `YYYY`
- `YYYY-MM`
- `YYYY-MM-DD`

Missing `endDate` does not automatically mean current employment.

### 4.3 Education

```json
{
  "institution": "Example University",
  "degree": "Bachelor's Degree",
  "fieldOfStudy": "Computer Science",
  "startDate": "2024",
  "endDate": "2027"
}
```

### 4.4 Projects

```json
{
  "name": "Portfolio Generator",
  "description": "AI-powered personal website generation platform.",
  "url": "https://github.com/example/portfolio-generator",
  "technologies": [
    "Python",
    "React",
    "PostgreSQL"
  ]
}
```

### 4.5 Certifications

```json
{
  "name": "Example Certification",
  "issuer": "Example Organization",
  "date": "2026-05"
}
```

### 4.6 Languages

```json
{
  "name": "English",
  "proficiency": "B2"
}
```

### 4.7 Volunteering and Awards

Volunteering entries may include:

- `organization`
- `role`
- `description`
- `startDate`
- `endDate`

Award entries may include:

- `name`
- `issuer`
- `date`
- `description`

### 4.8 Missing Information

The following rules apply:

- Unknown optional fields should be omitted.
- An empty array may be used when a category is explicitly known to contain no entries.
- Missing information must never be invented.
- AI-generated summaries must remain faithful to the provided source.
- Date precision must be preserved whenever possible.
- Unsupported assumptions must not be represented as verified facts.

For example, the absence of a certifications section in a CV does not prove that the user has no certifications.

---

## 5. CV Extraction Result Contract

**Contract Name:** `CVExtractionResult`  
**Producer:** CV Extraction Service  
**Consumer:** Core Backend / Profile Aggregation Module  
**Storage:** Private Amazon S3

### 5.1 Purpose

Defines the structured output produced when the CV Extraction Service processes an uploaded CV.

The result must contain the processing metadata and a professional profile following the canonical structure.

### 5.2 JSON Structure

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
    "skills": [
      "Java",
      "Python",
      "PostgreSQL"
    ],
    "projects": [
      {
        "name": "Portfolio Platform",
        "description": "Personal portfolio generation application.",
        "technologies": [
          "Java",
          "React"
        ]
      }
    ]
  }
}
```

### 5.3 Processing Rules

The CV Extraction Service must:

1. Extract information from the uploaded document.
2. Identify available professional information.
3. Normalize the extracted values into the canonical structure.
4. Preserve the meaning of the original document.
5. Avoid adding unsupported skills, projects, or experiences.
6. Validate the result against the agreed JSON Schema.
7. Store the structured result in private S3 storage.

**Expected S3 Object Key**

`job-456/task-789/cv.json`

After storing the result, the service publishes `processing.completed` containing the corresponding S3 object key.

---

## 6. LinkedIn Extraction Result Contract

**Contract Name:** `LinkedInExtractionResult`  
**Producer:** LinkedIn Extraction Service  
**Consumer:** Core Backend / Profile Aggregation Module  
**Storage:** Private Amazon S3

### 6.1 Purpose

Defines the structured output produced from a user-exported LinkedIn profile PDF.

The LinkedIn Extraction Service uses the same canonical professional profile structure as the CV Extraction Service.

This prevents the Profile Aggregation Module from needing completely separate data models for overlapping professional information.

### 6.2 JSON Structure

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
    "skills": [
      "Java",
      "Spring Boot",
      "Docker"
    ],
    "certifications": []
  }
}
```

### 6.3 Processing Rules

The LinkedIn Extraction Service must:

1. Retrieve the user-uploaded LinkedIn PDF.
2. Extract the available textual information.
3. Identify professional and academic information.
4. Convert the information into the canonical profile structure.
5. Preserve source-supported descriptions.
6. Validate the result against the agreed schema.
7. Store the result in private S3 storage.

**Expected S3 Object Key**

`job-456/task-791/linkedin.json`

The service must not retrieve LinkedIn information through automated scraping.

A LinkedIn profile URL alone is not a valid extraction input for the MVP.

The service does not access or modify the Core Backend database.

---

## 7. GitHub Analysis Result Contract

**Contract Name:** `GitHubAnalysisResult`  
**Producer:** GitHub Analysis Service  
**Consumer:** Core Backend / Profile Aggregation Module  
**Storage:** Private Amazon S3

### 7.1 Purpose

Defines structured information extracted from a user's public GitHub repositories.

Unlike CV and LinkedIn extraction, GitHub analysis produces repository-oriented information.

The result includes:

- GitHub username.
- Repository metadata.
- Project descriptions.
- Identified technologies.
- Documented functionality.
- Relevant directory structures.
- Technical evidence supporting extracted information.

The analysis uses a server-side GitHub token and public data only. No user GitHub token is stored or passed in any event.

### 7.2 JSON Structure

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
          "evidence": [
            {
              "kind": "GITHUB_METADATA",
              "reference": "primaryLanguage"
            }
          ]
        },
        {
          "name": "Maven",
          "certainty": "INFERRED",
          "evidence": [
            {
              "kind": "FILE_PATH",
              "path": "pom.xml"
            }
          ]
        }
      ],
      "features": [
        "User authentication",
        "Portfolio management"
      ],
      "structure": [
        "src/main/java/",
        "pom.xml",
        "Dockerfile",
        "README.md"
      ],
      "projectSummary": "A Java backend project for managing portfolio information."
    }
  ]
}
```

### 7.3 Repository Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| name | String | Yes | Repository name |
| url | String | Yes | GitHub repository URL |
| description | String | No | GitHub repository description |
| primaryLanguage | String | No | Language reported by GitHub |
| technologies | Array of objects | No | Identified technologies |
| features | Array of strings | No | Documented project features |
| structure | Array of strings | No | Relevant files and directories |
| projectSummary | String | No | Evidence-supported project summary |

The exact minimum repository information is enforced by the JSON Schema.

### 7.4 Technology Identification

A technology object contains:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| name | String | Yes | Technology name |
| certainty | Enum | Yes | OBSERVED or INFERRED |
| evidence | Array | Yes | Supporting technical evidence |

**Certainty Values**

`OBSERVED` — The technology is directly reported by GitHub metadata or explicitly identified in inspected documentation or files.

`INFERRED` — The technology is suggested by indirect evidence, such as repository structure or configuration filenames.

An inferred technology must not automatically be treated as a verified professional skill.

For example:

- `pom.xml` suggests Maven.
- `Dockerfile` indicates Docker-related configuration.
- `src/main/java` suggests a Java project structure.

These signals do not prove the use of a particular framework or architectural pattern.

### 7.5 Technical Evidence

Evidence entries identify the source supporting a technical observation.

**Evidence Fields**

| Field | Type | Description |
| --- | --- | --- |
| kind | Enum | Evidence category |
| path | String | Repository-relative file path, when applicable |
| reference | String | Metadata field or other source reference, when applicable |
| url | String | Source URL, when available |

Evidence categories:

- `GITHUB_METADATA`
- `FILE_PATH`
- `README`

### 7.6 Processing Rules

The GitHub Analysis Service must:

1. Retrieve the user's public repositories.
2. Retrieve repository metadata.
3. Inspect relevant directory structures and filenames.
4. Retrieve README documentation when available.
5. Identify technologies and documented features.
6. Distinguish observed information from inferred information.
7. Produce structured repository analysis results.
8. Validate the output against the agreed schema.
9. Store the result in private S3 storage.

**Expected S3 Object Key**

`job-456/task-790/github.json`

The MVP does not require cloning repositories, executing source code, or analyzing private repositories.

---

## 8. Unified Profile Contract

**Contract Name:** `UnifiedProfile`  
**Producer:** Core Backend / Profile Aggregation Module  
**Consumer:** Website Service / Website Generator Module  
**Storage:** PostgreSQL JSONB

### 8.1 Purpose

The Unified Profile combines structured information extracted from the user's available data sources.

It represents the consolidated professional profile used by the Website Service to generate a personalized portfolio website.

The Profile Aggregation Module is responsible for:

- Combining source-specific results.
- Removing duplicate information.
- Reconciling overlapping information.
- Normalizing professional information.
- Preserving supporting evidence.
- Producing one unified profile.

### 8.2 JSON Structure

```json
{
  "schemaVersion": 1,
  "sourceTypes": [
    "CV",
    "GITHUB",
    "LINKEDIN"
  ],
  "profile": {
    "fullName": "Alex Popescu",
    "headline": "Software Engineering Student",
    "location": "Cluj-Napoca, Romania",
    "summary": "Computer Science student with experience in backend development.",
    "workExperience": [
      {
        "company": "Example Company",
        "position": "Software Developer Intern",
        "description": "Backend development using Java.",
        "startDate": "2026-07",
        "endDate": "2026-09",
        "isCurrent": false
      }
    ],
    "education": [
      {
        "institution": "Example University",
        "degree": "Bachelor's Degree",
        "fieldOfStudy": "Computer Science"
      }
    ],
    "skills": [
      "Java",
      "Python",
      "PostgreSQL",
      "Docker"
    ],
    "projects": [
      {
        "name": "portfolio-api",
        "url": "https://github.com/example-user/portfolio-api",
        "description": "Backend API for portfolio management.",
        "technologies": [
          "Java",
          "Maven"
        ]
      }
    ]
  },
  "provenance": [
    {
      "path": "/profile/skills/3",
      "sourceType": "GITHUB",
      "taskId": "task-790",
      "reference": "portfolio-api/Dockerfile"
    }
  ]
}
```

### 8.3 Unified Profile Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| schemaVersion | Integer | Yes | Unified profile schema version |
| sourceTypes | Array of enums | Yes | Successfully processed input sources |
| profile | Object | Yes | Canonical professional profile |
| provenance | Array of objects | No | Supporting source references |

`sourceTypes` lists only the sources that completed. A failed optional source is absent from it and recorded as a job warning (§3.4).

### 8.4 Data Aggregation Rules

**Source Combination**

The Profile Aggregation Module processes only the sources submitted by the user.

For example:

- CV only: aggregate CV information.
- CV + GitHub: combine CV and repository information.
- CV + LinkedIn: combine both professional information sources.
- CV + GitHub + LinkedIn: combine all three.

Missing or failed optional sources must not prevent successful aggregation. The CV is required.

**Deduplication**

Duplicate information must be identified and consolidated.

Examples include:

- The same company and position appearing in CV and LinkedIn.
- The same technical skill appearing in multiple sources.
- The same GitHub project already described in the CV.

**Conflict Resolution**

When sources contain conflicting information, the aggregator must follow the reconciliation policy documented for the Core Backend Service.

Conflicting values must not be resolved through arbitrary assumptions.

**Technical Skills**

Skills explicitly stated in source documents should be distinguished from technologies inferred through GitHub analysis.

Inferred technologies should not be promoted to verified professional skills without supporting evidence.

### 8.5 Provenance

Provenance identifies which source supports information in the unified profile.

**Structure**

```json
{
  "path": "/profile/skills/3",
  "sourceType": "GITHUB",
  "taskId": "task-790",
  "reference": "portfolio-api/Dockerfile"
}
```

The `path` field uses JSON Pointer notation to identify a value in the stored unified profile.

If profile arrays are reordered during aggregation, provenance references must be updated to match the final stored document.

The provenance model must support tracing important information back to the relevant extraction result or technical evidence.

### 8.6 Storage

The unified profile is stored in the Core Backend PostgreSQL database.

**Table:** `profiles`  
**JSONB Column:** `profile_data`

The Website Service reads the unified profile but does not modify profile records owned by the Core Backend.

After successfully storing the profile, the Profile Aggregation Module publishes `profile.ready`.

---

## 9. Website Draft Contract

**Contract Name:** `WebsiteDraft`  
**Producer:** Website Service / Website Generator Module  
**Consumer:** Core Backend / Frontend  
**Storage:** PostgreSQL JSONB

### 9.1 Purpose

Defines the structured representation of a generated personal website before publication.

The Website Generator transforms a unified professional profile into a website draft compatible with the selected template.

The draft is stored by the Website Service and returned through the preview HTTP API.

### 9.2 JSON Structure

```json
{
  "schemaVersion": 1,
  "content": {
    "sections": [
      {
        "id": "hero",
        "type": "HERO",
        "data": {
          "title": "Alex Popescu",
          "subtitle": "Software Engineering Student"
        }
      },
      {
        "id": "about",
        "type": "ABOUT",
        "data": {
          "text": "Computer Science student passionate about backend development and AI systems."
        }
      },
      {
        "id": "skills",
        "type": "SKILLS",
        "data": {
          "items": [
            "Java",
            "Python",
            "PostgreSQL"
          ]
        }
      },
      {
        "id": "projects",
        "type": "PROJECTS",
        "data": {
          "items": [
            {
              "name": "portfolio-api",
              "description": "Backend API for managing portfolio information.",
              "url": "https://github.com/example-user/portfolio-api"
            }
          ]
        }
      }
    ]
  }
}
```

### 9.3 Website Draft Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| schemaVersion | Integer | Yes | Draft schema version |
| content | Object | Yes | Structured website content |

**`WebsitePreview`** is the preview API response. It is built by the Website Service from the columns and the stored draft:

```json
{
  "schemaVersion": 1,
  "websiteId": "website-456",
  "profileId": "profile-456",
  "templateId": "classic",
  "templateVersion": "1.0.0",
  "status": "PREVIEW_READY",
  "content": { "sections": [] }
}
```

The database columns (`template_id`, `template_version`, `status`) are authoritative; ids inside the JSON are informational.

### 9.4 Website Sections

The draft representation separates the selected template from its content.

Each section includes:

| Field | Type | Description |
| --- | --- | --- |
| id | String | Unique section identifier within the draft |
| type | String | Section category |
| data | Object | Template-compatible section content |

**Section Types**

- `HERO`
- `ABOUT`
- `EXPERIENCE`
- `EDUCATION`
- `SKILLS`
- `PROJECTS`
- `CONTACT`

The required data fields of each section are defined by the template's content schema and the shared JSON Schema.

### 9.5 Generation Rules

The Website Generator must:

1. Retrieve the unified profile.
2. Retrieve the selected website template.
3. Generate or adapt content using the AI provider.
4. Preserve factual information from the unified profile.
5. Produce template-compatible structured content.
6. Validate the draft against the agreed schema.
7. Store the draft in PostgreSQL.
8. Publish `website.generated`.

Generated descriptions may improve presentation and readability, but must not invent unsupported professional experience, qualifications, or achievements.

### 9.6 Preview Rules

The Core Backend retrieves the website draft through:

`GET /internal/websites/{websiteId}/preview`

The Frontend retrieves it through:

`GET /api/websites/{websiteId}/preview`

Both endpoints return `WebsitePreview` (§9.3).

Structured content is rendered using predefined templates and components.

AI-generated content must not be treated as trusted executable code.

The website remains unpublished during preview.

### 9.7 Publishing

After user approval, publishing runs asynchronously. The publish request returns `202 Accepted` and the website moves to `PUBLISHING`. The Website Publisher then sends the approved draft to the render worker, which converts it into deployable static website files.

The published output consists of:

- HTML
- CSS
- Static assets

These files are uploaded to the private published-websites S3 bucket, with `index.html` uploaded last so a site never goes live half-uploaded.

The published website is served through Amazon CloudFront.

The complete website draft is not included in the `website.publish.requested` or `website.published` SQS events.

---

## 10. Storage Contracts

### 10.1 Amazon S3 Buckets

The architecture uses three logical storage categories.

| Bucket | Purpose | Primary Writer |
| --- | --- | --- |
| `portfolio-uploads` | Uploaded CV and LinkedIn documents | Core Backend |
| `extraction-results` | Structured extraction and analysis results | AI Processing Services |
| `published-websites` | Published static website files | Website Service |

Actual bucket names may vary by environment.

### 10.2 Object Key Structure

**Uploaded Documents**

```
portfolio-uploads/
  user-123/
    job-456/
      cv.pdf
      linkedin-profile.pdf
```

**Extraction Results**

```
extraction-results/
  job-456/
    task-789/
      cv.json
    task-790/
      github.json
    task-791/
      linkedin.json
```

**Published Websites**

```
published-websites/
  alex-popescu/
    index.html
    assets/
      style.css
      script.js
```

In these examples, the top-level names represent logical S3 buckets.

SQS fields such as `cvS3Key` and `resultS3Key` contain object keys relative to their configured buckets.

For example:

`resultS3Key = "job-456/task-789/cv.json"`

Consumers must not automatically prepend a bucket name that is already configured separately.

### 10.3 Storage Validation Rules

- Uploaded documents must remain private.
- Extraction results must be valid JSON.
- Extraction results must be validated before publication of completion events.
- S3 object keys must not allow unauthorized resource access.
- Processing services must not directly modify Core Backend tables.
- Website Service must not modify Core-owned profile records.
- The Core Backend must not directly modify Website Service-owned website records.
- Published assets must be accessible through the configured CloudFront origin, not through unrestricted public bucket access.

---

## 11. Data Validation and Consistency

### 11.1 Schema Validation

Each service must validate produced and consumed data against the corresponding shared JSON Schema.

The MVP uses `schemaVersion: 1`.

Validation must cover:

- Required fields.
- Field types.
- Enum values.
- Supported date representations.
- URL formats.
- Nested object structures.
- Required processing identifiers.

### 11.2 Referential Consistency

The following relationships must remain valid:

- Each `taskId` belongs to the specified `jobId`.
- Each processing result matches its original `sourceType`.
- Each `profileId` belongs to the corresponding user and job.
- Each website references an existing unified profile (one website per profile).
- Each website uses a valid template identifier and version.

### 11.3 Duplicate Handling

The system must not create duplicate logical results due to repeated SQS deliveries.

A successfully completed task must have one authoritative extraction result.

Profile aggregation must not create duplicate profiles for the same logical aggregation operation.

Website generation must not create multiple websites due solely to repeated `profile.ready` messages.

Publishing must not run twice due to repeated `website.publish.requested` messages.

### 11.4 Data Integrity

- Extracted information must remain faithful to its source.
- Missing fields must not be fabricated.
- Cross-source conflicts must follow an explicit aggregation policy.
- AI-generated content must not introduce unsupported facts.
- Source evidence must be preserved where available.

---

## 12. Privacy and Security

CV and LinkedIn extraction results may contain personal information.

All services must follow the application's privacy and access-control requirements.

**Security Requirements**

- Store original documents and extraction results privately.
- Apply least-privilege access to S3 objects.
- Restrict access to unified user profiles.
- Avoid logging complete documents or sensitive profile contents.
- Never include OAuth credentials or access tokens in extraction results or events.
- Do not expose private contact information in published websites without appropriate authorization and user approval.
- Treat uploaded documents and external GitHub content as untrusted inputs.
- Validate generated website content before rendering or publishing.
- `DELETE /api/me` removes the user's uploads, extraction results, profile data and published sites.

If external AI providers process personal information, the integration must respect the application's privacy requirements and user consent.

---

## 13. Contract Ownership and Versioning

Each data contract has a clearly defined owner.

| Contract | Owner |
| --- | --- |
| CVExtractionResult | CV Extraction Service |
| LinkedInExtractionResult | LinkedIn Extraction Service |
| GitHubAnalysisResult | GitHub Analysis Service |
| CanonicalProfessionalProfile | Shared contract — Core Backend coordinates |
| UnifiedProfile | Core Backend / Profile Aggregation |
| WebsiteDraft | Website Service |

### 13.1 Versioning Rules

- All initial contracts use `schemaVersion: 1`.
- Compatible additions may preserve the existing major version.
- Breaking structural changes require a new contract version.
- Producers and consumers must coordinate incompatible changes.
- Contract compatibility must be verified before deployment.

### 13.2 Machine-Readable Schemas

The authoritative JSON Schemas are stored in GitHub under the shared `contracts/` directory.

Structure:

```
contracts/
  schemas/
    common/
      professional-profile.schema.json
    extraction/
      cv-result.schema.json
      linkedin-result.schema.json
      github-result.schema.json
    profile/
      unified-profile.schema.json
    website/
      website-draft.schema.json
```

These schemas are used for automated validation and contract testing.

Confluence provides human-readable documentation, while the version-controlled JSON Schemas represent the executable technical contracts.

---

## 14. Out of Scope for v1

The following are deliberately not part of the v1 contracts:

- Editing the unified profile or the website draft before publishing (preview is read-only).
- Profile photos and other user-uploaded media in the website draft.
- Third-party or user-supplied templates; templates are versioned packages in the repository.
- Slug renaming after the first publish.
- Reprocessing of old extraction results; results are immutable per task, and a retry creates a new attempt.
