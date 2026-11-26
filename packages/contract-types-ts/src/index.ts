/* eslint-disable */
/**
 * GENERATED FILE - DO NOT EDIT.
 * Source: contracts/schemas. Regenerate with `make contracts-types`
 * (or `npm run types` in contracts/tooling).
 */

/**
 * The single error-code enum for every event and HTTP error body. Failure Handling Design §3.4, Shared Data Contracts §3.3. Services may add codes but never repurpose one.
 */
export type ErrorCode =
  | "SOURCE_UNREADABLE"
  | "SOURCE_NOT_FOUND"
  | "SOURCE_EMPTY"
  | "AI_OUTPUT_INVALID"
  | "AI_PROVIDER_UNAVAILABLE"
  | "EXTERNAL_RATE_LIMITED"
  | "STORAGE_ERROR"
  | "INTERNAL_ERROR"
  | "TIMEOUT"
  | "RETRIES_EXHAUSTED"
  | "SLUG_TAKEN"
  | "SLUG_CONFLICT"
  | "PUBLISH_ASSET_ERROR"
  | "JOB_NOT_RETRYABLE"
  | "RATE_LIMITED";
/**
 * Where a failure happened. Failure Handling Design §3.1.
 */
export type FailureStage =
  | "CV_EXTRACTION"
  | "GITHUB_ANALYSIS"
  | "LINKEDIN_EXTRACTION"
  | "WEBSITE_GENERATION"
  | "WEBSITE_PUBLISHING";
/**
 * jobs.status, owned by Core Backend. Failure Handling Design §6.1.
 */
export type JobStatus =
  | "QUEUED"
  | "PROCESSING"
  | "AGGREGATING"
  | "GENERATING"
  | "PREVIEW_READY"
  | "PUBLISHING"
  | "PUBLISHED"
  | "FAILED";
/**
 * Information source of a processing task. Shared Data Contracts §3.1.
 */
export type SourceType = "CV" | "GITHUB" | "LINKEDIN";
/**
 * job_tasks.status, owned by Core Backend. Failure Handling Design §6.2.
 */
export type TaskStatus = "PENDING" | "COMPLETED" | "FAILED";
/**
 * websites.status, owned by Website Service. Failure Handling Design §6.3 plus UNPUBLISHED (slug takeover, Database Architecture §5.10, Website Service).
 */
export type WebsiteStatus =
  | "GENERATING"
  | "GENERATION_FAILED"
  | "PREVIEW_READY"
  | "PUBLISHING"
  | "PUBLISH_FAILED"
  | "PUBLISHED"
  | "UNPUBLISHED";

/**
 * Queue `cv-extraction`. Producer: Core Backend (Job Orchestrator). Consumer: CV Extraction Service. SQS Event Contracts §4.1.
 */
export interface CvExtractRequested {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Unique per emission (UUID).
   */
  eventId: string;
  /**
   * UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.
   */
  occurredAt: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  event: "cv.extract.requested";
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  taskId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  userId: string;
  /**
   * Object key relative to its bucket, for example user-123/job-456/cv.pdf. No leading slash.
   */
  cvS3Key: string;
  /**
   * Retry attempt number (default 1). Request events may carry it; result and failure events echo it.
   */
  attempt?: number;
}
/**
 * Queue `github-analysis`. Producer: Core Backend (Job Orchestrator). Consumer: GitHub Analysis Service. SQS Event Contracts §4.2.
 */
export interface GithubAnalyzeRequested {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Unique per emission (UUID).
   */
  eventId: string;
  /**
   * UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.
   */
  occurredAt: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  event: "github.analyze.requested";
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  taskId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  userId: string;
  /**
   * Normalized GitHub username (GitHub allows letters, digits and single hyphens, at most 39 characters).
   */
  githubUsername: string;
  /**
   * Retry attempt number (default 1). Request events may carry it; result and failure events echo it.
   */
  attempt?: number;
}
/**
 * Queue `linkedin-extraction`. Producer: Core Backend (Job Orchestrator). Consumer: LinkedIn Extraction Service. SQS Event Contracts §4.3.
 */
export interface LinkedinExtractRequested {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Unique per emission (UUID).
   */
  eventId: string;
  /**
   * UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.
   */
  occurredAt: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  event: "linkedin.extract.requested";
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  taskId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  userId: string;
  /**
   * Object key relative to its bucket, for example user-123/job-456/cv.pdf. No leading slash.
   */
  linkedinS3Key: string;
  /**
   * Retry attempt number (default 1). Request events may carry it; result and failure events echo it.
   */
  attempt?: number;
}
/**
 * Queue `processing-results`. Producer: CV / GitHub / LinkedIn services. Consumer: Core Backend (Job Orchestrator). SQS Event Contracts §5.1.
 */
export interface ProcessingCompleted {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Unique per emission (UUID).
   */
  eventId: string;
  /**
   * UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.
   */
  occurredAt: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  event: "processing.completed";
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  taskId: string;
  sourceType: SourceType;
  status: "COMPLETED";
  /**
   * Object key relative to its bucket, for example user-123/job-456/cv.pdf. No leading slash.
   */
  resultS3Key: string;
  /**
   * Retry attempt number (default 1). Request events may carry it; result and failure events echo it.
   */
  attempt?: number;
}
/**
 * Queue `processing-results`. Producer: CV / GitHub / LinkedIn services. Consumer: Core Backend (Job Orchestrator). SQS Event Contracts §5.2; Failure Handling Design §3.2.
 */
export interface ProcessingFailed {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Unique per emission (UUID).
   */
  eventId: string;
  /**
   * UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.
   */
  occurredAt: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  event: "processing.failed";
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  taskId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  userId: string;
  sourceType: SourceType;
  stage: FailureStage & ("CV_EXTRACTION" | "GITHUB_ANALYSIS" | "LINKEDIN_EXTRACTION");
  errorCode: ErrorCode;
  /**
   * Short, safe to show to a user. No stack traces, CV text, personal data or secrets.
   */
  errorMessage: string;
  /**
   * Whether the user can reasonably retry as is.
   */
  retryable: boolean;
  /**
   * Processing attempts made before giving up.
   */
  attempts: number;
  /**
   * Object key relative to its bucket, for example user-123/job-456/cv.pdf. No leading slash.
   */
  diagnosticsS3Key?: string;
  /**
   * Retry attempt number (default 1). Request events may carry it; result and failure events echo it.
   */
  attempt?: number;
}
/**
 * Queue `website-generation`. Producer: Core Backend (Profile Aggregator). Consumer: Website Service (Website Generator). SQS Event Contracts §6.1.
 */
export interface ProfileReady {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Unique per emission (UUID).
   */
  eventId: string;
  /**
   * UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.
   */
  occurredAt: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  event: "profile.ready";
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  userId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  profileId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  templateId: string;
}
/**
 * Queue `processing-results`. Producer: Website Service (Generator or Publisher). Consumer: Core Backend (Job Orchestrator). SQS Event Contracts §6.5; Failure Handling Design §3.3.
 */
export interface WebsiteFailed {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Unique per emission (UUID).
   */
  eventId: string;
  /**
   * UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.
   */
  occurredAt: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  event: "website.failed";
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  userId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  profileId: string;
  /**
   * Absent when the failure happened before the websites row was created.
   */
  websiteId?: string;
  stage: FailureStage & ("WEBSITE_GENERATION" | "WEBSITE_PUBLISHING");
  errorCode: ErrorCode;
  /**
   * Short, safe to show to a user. No stack traces, CV text, personal data or secrets.
   */
  errorMessage: string;
  /**
   * Whether the user can reasonably retry as is.
   */
  retryable: boolean;
  /**
   * Processing attempts made before giving up.
   */
  attempts: number;
  /**
   * Object key relative to its bucket, for example user-123/job-456/cv.pdf. No leading slash.
   */
  diagnosticsS3Key?: string;
}
/**
 * Queue `processing-results`. Producer: Website Service (Website Generator). Consumer: Core Backend (Job Orchestrator). SQS Event Contracts §6.2.
 */
export interface WebsiteGenerated {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Unique per emission (UUID).
   */
  eventId: string;
  /**
   * UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.
   */
  occurredAt: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  event: "website.generated";
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  userId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  profileId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  websiteId: string;
  status: "PREVIEW_READY";
}
/**
 * Queue `processing-results`. Producer: Website Service (Website Publisher). Consumer: Core Backend. SQS Event Contracts §6.4.
 */
export interface WebsitePublished {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Unique per emission (UUID).
   */
  eventId: string;
  /**
   * UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.
   */
  occurredAt: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  event: "website.published";
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  userId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  websiteId: string;
  /**
   * Subdomain slug: lowercase letters, digits and hyphens, a valid DNS label of at most 63 characters. Website Service doc.
   */
  slug: string;
  status: "PUBLISHED";
  /**
   * Absolute https URL.
   */
  url: string;
}
/**
 * Queue `website-publishing`. Producer: Website Service (transactional outbox). Consumer: Website Service (Website Publisher). SQS Event Contracts §6.3.
 */
export interface WebsitePublishRequested {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Unique per emission (UUID).
   */
  eventId: string;
  /**
   * UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.
   */
  occurredAt: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  event: "website.publish.requested";
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  userId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  websiteId: string;
  /**
   * Subdomain slug: lowercase letters, digits and hyphens, a valid DNS label of at most 63 characters. Website Service doc.
   */
  slug: string;
}
