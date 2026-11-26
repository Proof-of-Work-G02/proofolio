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
 * Website draft section types. Shared Data Contracts §9.4.
 */
export type SectionType =
  "HERO" | "ABOUT" | "EXPERIENCE" | "EDUCATION" | "SKILLS" | "PROJECTS" | "CONTACT";
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
 * `data` of a ABOUT section in a website draft. text from summary. Plain text only; URLs must be https. Template System Spec §5.
 */
export interface AboutSectionData {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  text: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  location?: string;
}
/**
 * Shared Data Contracts §4.7.
 */
export interface Award {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  name?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  issuer?: string;
  /**
   * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
   */
  date?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  description?: string;
}
/**
 * Shared professional structure produced by the CV and LinkedIn extractors and used inside the unified profile. Every field is optional: omit what is unknown, never invent it (Shared Data Contracts §4, §4.8). An empty array means the category is known to be empty.
 */
export interface CanonicalProfessionalProfile {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  fullName?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  headline?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  location?: string;
  /**
   * Email address.
   */
  email?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  phone?: string;
  /**
   * Professional URLs.
   *
   * Items: Absolute https URL.
   */
  links?: string[];
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  summary?: string;
  workExperience?: WorkExperience[];
  education?: Education[];
  /**
   * Items: Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  skills?: string[];
  projects?: Project[];
  certifications?: Certification[];
  languages?: Language[];
  volunteering?: Volunteering[];
  awards?: Award[];
}
/**
 * Shared Data Contracts §4.2. A missing endDate does not mean current employment.
 */
export interface WorkExperience {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  company?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  position?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  description?: string;
  /**
   * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
   */
  startDate?: string;
  /**
   * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
   */
  endDate?: string;
  isCurrent?: boolean;
}
/**
 * Shared Data Contracts §4.3.
 */
export interface Education {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  institution?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  degree?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  fieldOfStudy?: string;
  /**
   * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
   */
  startDate?: string;
  /**
   * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
   */
  endDate?: string;
}
/**
 * Shared Data Contracts §4.4.
 */
export interface Project {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  name?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  description?: string;
  /**
   * Absolute https URL.
   */
  url?: string;
  /**
   * Items: Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  technologies?: string[];
}
/**
 * Shared Data Contracts §4.5.
 */
export interface Certification {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  name?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  issuer?: string;
  /**
   * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
   */
  date?: string;
}
/**
 * Shared Data Contracts §4.6.
 */
export interface Language {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  name: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  proficiency?: string;
}
/**
 * Shared Data Contracts §4.7.
 */
export interface Volunteering {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  organization?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  role?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  description?: string;
  /**
   * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
   */
  startDate?: string;
  /**
   * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
   */
  endDate?: string;
}
/**
 * `data` of a CONTACT section in a website draft. At least one field. Plain text only; URLs must be https. Template System Spec §5.
 */
export interface ContactSectionData {
  /**
   * Email address.
   */
  email?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  phone?: string;
  /**
   * @minItems 1
   */
  links?: [Link, ...Link[]];
}
/**
 * A labelled https link.
 */
export interface Link {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  label: string;
  /**
   * Absolute https URL.
   */
  url: string;
}
/**
 * Output of the CV Extraction Service, key <jobId>/<taskId>/cv.json. Stored in the extraction-results bucket. Shared Data Contracts §3, §5.
 */
export interface CVExtractionResult {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  taskId: string;
  sourceType: "CV";
  profile: CanonicalProfessionalProfile;
}
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
 * `data` of a EDUCATION section in a website draft. From education; omit the section when empty. Plain text only; URLs must be https. Template System Spec §5.
 */
export interface EducationSectionData {
  /**
   * @minItems 1
   */
  items: [
    {
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      institution: string;
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      degree?: string;
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      fieldOfStudy?: string;
      /**
       * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
       */
      startDate?: string;
      /**
       * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
       */
      endDate?: string;
    },
    ...{
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      institution: string;
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      degree?: string;
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      fieldOfStudy?: string;
      /**
       * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
       */
      startDate?: string;
      /**
       * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
       */
      endDate?: string;
    }[]
  ];
}
/**
 * Shared Data Contracts §7.5.
 */
export interface Evidence {
  kind: "GITHUB_METADATA" | "FILE_PATH" | "README";
  /**
   * Repository-relative file path.
   */
  path?: string;
  /**
   * Metadata field or other source reference.
   */
  reference?: string;
  /**
   * Absolute https URL.
   */
  url?: string;
}
/**
 * `data` of a EXPERIENCE section in a website draft. From workExperience; omit the section when empty. Plain text only; URLs must be https. Template System Spec §5.
 */
export interface ExperienceSectionData {
  /**
   * @minItems 1
   */
  items: [
    {
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      company: string;
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      position: string;
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      description?: string;
      /**
       * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
       */
      startDate: string;
      /**
       * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
       */
      endDate?: string;
      isCurrent?: boolean;
    },
    ...{
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      company: string;
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      position: string;
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      description?: string;
      /**
       * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
       */
      startDate: string;
      /**
       * Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).
       */
      endDate?: string;
      isCurrent?: boolean;
    }[]
  ];
}
/**
 * Output of the GitHub Analysis Service, key <jobId>/<taskId>/github.json. Public data only. Stored in the extraction-results bucket. Shared Data Contracts §3, §7.
 */
export interface GitHubAnalysisResult {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  taskId: string;
  sourceType: "GITHUB";
  /**
   * Normalized GitHub username (GitHub allows letters, digits and single hyphens, at most 39 characters).
   */
  githubUsername: string;
  repositories: Repository[];
}
/**
 * Shared Data Contracts §7.3.
 */
export interface Repository {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  name: string;
  /**
   * Absolute https URL.
   */
  url: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  description?: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  primaryLanguage?: string;
  technologies?: Technology[];
  /**
   * Items: Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  features?: string[];
  /**
   * Relevant files and directories.
   */
  structure?: string[];
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  projectSummary?: string;
}
/**
 * Shared Data Contracts §7.4.
 */
export interface Technology {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  name: string;
  /**
   * OBSERVED: reported by GitHub or explicit in inspected files. INFERRED: suggested by indirect evidence; never promoted to a verified skill on its own.
   */
  certainty: "OBSERVED" | "INFERRED";
  /**
   * @minItems 1
   */
  evidence: [Evidence, ...Evidence[]];
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
 * `data` of a HERO section in a website draft. title from fullName, subtitle from headline. Plain text only; URLs must be https. Template System Spec §5.
 */
export interface HeroSectionData {
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  title: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  subtitle?: string;
  links?: Link[];
}
/**
 * Output of the LinkedIn Extraction Service, key <jobId>/<taskId>/linkedin.json. Stored in the extraction-results bucket. Shared Data Contracts §3, §6.
 */
export interface LinkedInExtractionResult {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  jobId: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  taskId: string;
  sourceType: "LINKEDIN";
  profile: CanonicalProfessionalProfile;
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
 * `data` of a PROJECTS section in a website draft. From projects; omit the section when empty. Plain text only; URLs must be https. Template System Spec §5.
 */
export interface ProjectsSectionData {
  /**
   * @minItems 1
   */
  items: [
    {
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      name: string;
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      description?: string;
      /**
       * Absolute https URL.
       */
      url?: string;
      /**
       * Items: Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      technologies?: string[];
    },
    ...{
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      name: string;
      /**
       * Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      description?: string;
      /**
       * Absolute https URL.
       */
      url?: string;
      /**
       * Items: Plain text (no HTML or Markdown; the renderer escapes everything).
       */
      technologies?: string[];
    }[]
  ];
}
/**
 * Shared Data Contracts §8.5.
 */
export interface Provenance {
  /**
   * JSON Pointer into this document, for example /profile/skills/3. Updated if arrays are reordered.
   */
  path: string;
  sourceType: SourceType;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  taskId: string;
  /**
   * Pointer into the source result or evidence, for example portfolio-api/Dockerfile.
   */
  reference?: string;
}
/**
 * `data` of a SKILLS section in a website draft. From skills. Plain text only; URLs must be https. Template System Spec §5.
 */
export interface SkillsSectionData {
  /**
   * @minItems 1
   *
   * Items: Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  items: [string, ...string[]];
  groups?: {
    /**
     * Plain text (no HTML or Markdown; the renderer escapes everything).
     */
    label: string;
    /**
     * @minItems 1
     *
     * Items: Plain text (no HTML or Markdown; the renderer escapes everything).
     */
    items: [string, ...string[]];
  }[];
}
/**
 * template.json of a website template package (packages/templates/<id>/). Template System Spec §4.
 */
export interface TemplateManifest {
  /**
   * Readable template id, for example classic (Template System Spec §4).
   */
  id: string;
  /**
   * Semantic version, for example 1.0.0.
   */
  version: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  name: string;
  /**
   * Plain text (no HTML or Markdown; the renderer escapes everything).
   */
  description: string;
  /**
   * Thumbnail file name inside the template package.
   */
  thumbnail: string;
  /**
   * Layout kind, for example single-page.
   */
  layout: string;
  sections: {
    required: SectionType[];
    optional: SectionType[];
  };
  /**
   * Render order of the sections.
   *
   * @minItems 1
   */
  order: [SectionType, ...SectionType[]];
  /**
   * Per-section limits, for example PROJECTS: {maxItems: 6}. Stops the AI producing more than the layout holds.
   */
  limits?: {
    [k: string]:
      | {
          maxItems: number;
        }
      | undefined;
  };
  /**
   * Optional theme choices, unused in v1.
   */
  themeOptions?: {
    [k: string]: string[] | undefined;
  };
}
/**
 * Consolidated profile built by Core Backend aggregation, stored in profiles.profile_data (JSONB). Ids that are table columns (job, user, profile) are not repeated here; source warnings live in jobs.warnings. Shared Data Contracts §8.
 */
export interface UnifiedProfile {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Sources that completed. The CV is required, so it is always present; a failed optional source is absent.
   *
   * @minItems 1
   */
  sourceTypes: [SourceType, ...SourceType[]];
  profile: CanonicalProfessionalProfile;
  provenance?: Provenance[];
}
/**
 * Generated website content, stored in websites.draft_content (JSONB). The database columns (template_id, template_version, status) are authoritative; the ids here are informational. Shared Data Contracts §9, Template System Spec §5.
 */
export interface WebsiteDraft {
  /**
   * Major contract version. All MVP events use 1.
   */
  schemaVersion: 1;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  websiteId?: string;
  /**
   * Opaque identifier. Never parse or derive meaning from it.
   */
  profileId?: string;
  /**
   * Readable template id, for example classic (Template System Spec §4).
   */
  templateId?: string;
  /**
   * Semantic version, for example 1.0.0.
   */
  templateVersion?: string;
  status?: WebsiteStatus;
  content: {
    /**
     * Ordered sections. Section ids must be unique within the draft (checked by the generator, not expressible in JSON Schema).
     *
     * @minItems 1
     *
     * Items: One section: id, type and the data schema for that type.
     */
    sections: [
      (
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "HERO";
            data: HeroSectionData;
          }
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "ABOUT";
            data: AboutSectionData;
          }
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "EXPERIENCE";
            data: ExperienceSectionData;
          }
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "EDUCATION";
            data: EducationSectionData;
          }
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "SKILLS";
            data: SkillsSectionData;
          }
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "PROJECTS";
            data: ProjectsSectionData;
          }
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "CONTACT";
            data: ContactSectionData;
          }
      ),
      ...(
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "HERO";
            data: HeroSectionData;
          }
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "ABOUT";
            data: AboutSectionData;
          }
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "EXPERIENCE";
            data: ExperienceSectionData;
          }
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "EDUCATION";
            data: EducationSectionData;
          }
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "SKILLS";
            data: SkillsSectionData;
          }
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "PROJECTS";
            data: ProjectsSectionData;
          }
        | {
            /**
             * Unique section id within the draft, for example hero.
             */
            id: string;
            type: "CONTACT";
            data: ContactSectionData;
          }
      )[]
    ];
  };
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
