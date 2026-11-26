# GENERATED FILE - DO NOT EDIT.
# Source: contracts/schemas. Regenerate with `make contracts-types`
# (or `npm run types` in contracts/tooling).

from __future__ import annotations

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import (
    AnyUrl,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    RootModel,
)


class ProofolioContracts(BaseModel):
    pass


class AboutSectionData(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    text: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    location: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )


class Award(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    issuer: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    date: str | None = Field(
        None,
        description='Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).',
        pattern='^[0-9]{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01]))?)?$',
    )
    description: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )


class Link(RootModel[AnyUrl]):
    root: AnyUrl = Field(..., description='Absolute https URL.')


class Skill(RootModel[str]):
    root: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )


class Certification(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    issuer: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    date: str | None = Field(
        None,
        description='Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).',
        pattern='^[0-9]{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01]))?)?$',
    )


class CvExtractRequested(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    eventId: UUID = Field(..., description='Unique per emission (UUID).')
    occurredAt: AwareDatetime = Field(
        ..., description='UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    event: Literal['cv.extract.requested']
    taskId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    userId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    cvS3Key: str = Field(
        ...,
        description='Object key relative to its bucket, for example user-123/job-456/cv.pdf. No leading slash.',
        max_length=1024,
        min_length=1,
        pattern='^[^/]',
    )
    attempt: int | None = Field(
        None,
        description='Retry attempt number (default 1). Request events may carry it; result and failure events echo it.',
        ge=1,
    )


class Education(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    institution: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    degree: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    fieldOfStudy: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    startDate: str | None = Field(
        None,
        description='Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).',
        pattern='^[0-9]{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01]))?)?$',
    )
    endDate: str | None = Field(
        None,
        description='Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).',
        pattern='^[0-9]{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01]))?)?$',
    )


class Item(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    institution: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    degree: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    fieldOfStudy: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    startDate: str | None = Field(
        None,
        description='Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).',
        pattern='^[0-9]{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01]))?)?$',
    )
    endDate: str | None = Field(
        None,
        description='Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).',
        pattern='^[0-9]{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01]))?)?$',
    )


class EducationSectionData(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    items: list[Item] = Field(..., min_length=1)


class ErrorCode(StrEnum):
    SOURCE_UNREADABLE = 'SOURCE_UNREADABLE'
    SOURCE_NOT_FOUND = 'SOURCE_NOT_FOUND'
    SOURCE_EMPTY = 'SOURCE_EMPTY'
    AI_OUTPUT_INVALID = 'AI_OUTPUT_INVALID'
    AI_PROVIDER_UNAVAILABLE = 'AI_PROVIDER_UNAVAILABLE'
    EXTERNAL_RATE_LIMITED = 'EXTERNAL_RATE_LIMITED'
    STORAGE_ERROR = 'STORAGE_ERROR'
    INTERNAL_ERROR = 'INTERNAL_ERROR'
    TIMEOUT = 'TIMEOUT'
    RETRIES_EXHAUSTED = 'RETRIES_EXHAUSTED'
    SLUG_TAKEN = 'SLUG_TAKEN'
    SLUG_CONFLICT = 'SLUG_CONFLICT'
    PUBLISH_ASSET_ERROR = 'PUBLISH_ASSET_ERROR'
    JOB_NOT_RETRYABLE = 'JOB_NOT_RETRYABLE'
    RATE_LIMITED = 'RATE_LIMITED'


class Kind(StrEnum):
    GITHUB_METADATA = 'GITHUB_METADATA'
    FILE_PATH = 'FILE_PATH'
    README = 'README'


class Evidence(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    kind: Kind
    path: str | None = Field(
        None, description='Repository-relative file path.', min_length=1
    )
    reference: str | None = Field(
        None, description='Metadata field or other source reference.', min_length=1
    )
    url: AnyUrl | None = Field(None, description='Absolute https URL.')


class Item1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    company: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    position: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    description: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    startDate: str = Field(
        ...,
        description='Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).',
        pattern='^[0-9]{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01]))?)?$',
    )
    endDate: str | None = Field(
        None,
        description='Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).',
        pattern='^[0-9]{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01]))?)?$',
    )
    isCurrent: bool | None = None


class ExperienceSectionData(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    items: list[Item1] = Field(..., min_length=1)


class FailureStage(StrEnum):
    CV_EXTRACTION = 'CV_EXTRACTION'
    GITHUB_ANALYSIS = 'GITHUB_ANALYSIS'
    LINKEDIN_EXTRACTION = 'LINKEDIN_EXTRACTION'
    WEBSITE_GENERATION = 'WEBSITE_GENERATION'
    WEBSITE_PUBLISHING = 'WEBSITE_PUBLISHING'


class GithubAnalyzeRequested(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        regex_engine="python-re",
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    eventId: UUID = Field(..., description='Unique per emission (UUID).')
    occurredAt: AwareDatetime = Field(
        ..., description='UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    event: Literal['github.analyze.requested']
    taskId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    userId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    githubUsername: str = Field(
        ...,
        description='Normalized GitHub username (GitHub allows letters, digits and single hyphens, at most 39 characters).',
        pattern='^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$',
    )
    attempt: int | None = Field(
        None,
        description='Retry attempt number (default 1). Request events may carry it; result and failure events echo it.',
        ge=1,
    )


class JobStatus(StrEnum):
    QUEUED = 'QUEUED'
    PROCESSING = 'PROCESSING'
    AGGREGATING = 'AGGREGATING'
    GENERATING = 'GENERATING'
    PREVIEW_READY = 'PREVIEW_READY'
    PUBLISHING = 'PUBLISHING'
    PUBLISHED = 'PUBLISHED'
    FAILED = 'FAILED'


class Language(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    proficiency: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )


class LinkModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    label: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    url: AnyUrl = Field(..., description='Absolute https URL.')


class LinkedinExtractRequested(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    eventId: UUID = Field(..., description='Unique per emission (UUID).')
    occurredAt: AwareDatetime = Field(
        ..., description='UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    event: Literal['linkedin.extract.requested']
    taskId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    userId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    linkedinS3Key: str = Field(
        ...,
        description='Object key relative to its bucket, for example user-123/job-456/cv.pdf. No leading slash.',
        max_length=1024,
        min_length=1,
        pattern='^[^/]',
    )
    attempt: int | None = Field(
        None,
        description='Retry attempt number (default 1). Request events may carry it; result and failure events echo it.',
        ge=1,
    )


class ProfileReady(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    eventId: UUID = Field(..., description='Unique per emission (UUID).')
    occurredAt: AwareDatetime = Field(
        ..., description='UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    event: Literal['profile.ready']
    userId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    profileId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    templateId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )


class Technology(RootModel[str]):
    root: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )


class Project(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    description: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    url: AnyUrl | None = Field(None, description='Absolute https URL.')
    technologies: list[Technology] | None = None


class Item2(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    description: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    url: AnyUrl | None = Field(None, description='Absolute https URL.')
    technologies: list[Technology] | None = None


class ProjectsSectionData(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    items: list[Item2] = Field(..., min_length=1)


class Feature(RootModel[str]):
    root: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )


class StructureItem(RootModel[str]):
    root: str = Field(..., min_length=1)


class SectionType(StrEnum):
    HERO = 'HERO'
    ABOUT = 'ABOUT'
    EXPERIENCE = 'EXPERIENCE'
    EDUCATION = 'EDUCATION'
    SKILLS = 'SKILLS'
    PROJECTS = 'PROJECTS'
    CONTACT = 'CONTACT'


class Item3(RootModel[str]):
    root: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )


class Group(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    label: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    items: list[Item3] = Field(..., min_length=1)


class SkillsSectionData(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    items: list[Item3] = Field(..., min_length=1)
    groups: list[Group] | None = None


class SourceType(StrEnum):
    CV = 'CV'
    GITHUB = 'GITHUB'
    LINKEDIN = 'LINKEDIN'


class TaskStatus(StrEnum):
    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


class Certainty(StrEnum):
    OBSERVED = 'OBSERVED'
    INFERRED = 'INFERRED'


class TechnologyModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    certainty: Certainty = Field(
        ...,
        description='OBSERVED: reported by GitHub or explicit in inspected files. INFERRED: suggested by indirect evidence; never promoted to a verified skill on its own.',
    )
    evidence: list[Evidence] = Field(..., min_length=1)


class Sections(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    required: list[SectionType]
    optional: list[SectionType]


class Limits(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    maxItems: int = Field(..., ge=1)


class TemplateManifest(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(
        ...,
        description='Readable template id, for example classic (Template System Spec §4).',
        pattern='^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$',
    )
    version: str = Field(
        ...,
        description='Semantic version, for example 1.0.0.',
        pattern='^[0-9]+\\.[0-9]+\\.[0-9]+$',
    )
    name: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    description: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    thumbnail: str = Field(
        ...,
        description='Thumbnail file name inside the template package.',
        pattern='^[A-Za-z0-9._-]+\\.(webp|png|jpg|jpeg|svg)$',
    )
    layout: str = Field(
        ..., description='Layout kind, for example single-page.', min_length=1
    )
    sections: Sections
    order: list[SectionType] = Field(
        ..., description='Render order of the sections.', min_length=1
    )
    limits: dict[SectionType, Limits] | None = Field(
        None,
        description='Per-section limits, for example PROJECTS: {maxItems: 6}. Stops the AI producing more than the layout holds.',
    )
    themeOptions: dict[str, list[str]] | None = Field(
        None, description='Optional theme choices, unused in v1.'
    )


class Volunteering(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    organization: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    role: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    description: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    startDate: str | None = Field(
        None,
        description='Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).',
        pattern='^[0-9]{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01]))?)?$',
    )
    endDate: str | None = Field(
        None,
        description='Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).',
        pattern='^[0-9]{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01]))?)?$',
    )


class Sections2(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(
        ...,
        description='Unique section id within the draft, for example hero.',
        pattern='^[a-z0-9][a-z0-9-]{0,63}$',
    )
    type: Literal['ABOUT']
    data: AboutSectionData


class Sections3(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(
        ...,
        description='Unique section id within the draft, for example hero.',
        pattern='^[a-z0-9][a-z0-9-]{0,63}$',
    )
    type: Literal['EXPERIENCE']
    data: ExperienceSectionData


class Sections4(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(
        ...,
        description='Unique section id within the draft, for example hero.',
        pattern='^[a-z0-9][a-z0-9-]{0,63}$',
    )
    type: Literal['EDUCATION']
    data: EducationSectionData


class Sections5(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(
        ...,
        description='Unique section id within the draft, for example hero.',
        pattern='^[a-z0-9][a-z0-9-]{0,63}$',
    )
    type: Literal['SKILLS']
    data: SkillsSectionData


class Sections6(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(
        ...,
        description='Unique section id within the draft, for example hero.',
        pattern='^[a-z0-9][a-z0-9-]{0,63}$',
    )
    type: Literal['PROJECTS']
    data: ProjectsSectionData


class WebsiteFailed(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    eventId: UUID = Field(..., description='Unique per emission (UUID).')
    occurredAt: AwareDatetime = Field(
        ..., description='UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    event: Literal['website.failed']
    userId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    profileId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    websiteId: str | None = Field(
        None,
        description='Absent when the failure happened before the websites row was created.',
        max_length=128,
        min_length=1,
    )
    stage: FailureStage
    errorCode: ErrorCode
    errorMessage: str = Field(
        ...,
        description='Short, safe to show to a user. No stack traces, CV text, personal data or secrets.',
        max_length=500,
        min_length=1,
    )
    retryable: bool = Field(
        ..., description='Whether the user can reasonably retry as is.'
    )
    attempts: int = Field(
        ..., description='Processing attempts made before giving up.', ge=1
    )
    diagnosticsS3Key: str | None = Field(
        None,
        description='Object key relative to its bucket, for example user-123/job-456/cv.pdf. No leading slash.',
        max_length=1024,
        min_length=1,
        pattern='^[^/]',
    )


class WebsiteGenerated(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    eventId: UUID = Field(..., description='Unique per emission (UUID).')
    occurredAt: AwareDatetime = Field(
        ..., description='UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    event: Literal['website.generated']
    userId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    profileId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    websiteId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    status: Literal['PREVIEW_READY']


class WebsitePublished(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    eventId: UUID = Field(..., description='Unique per emission (UUID).')
    occurredAt: AwareDatetime = Field(
        ..., description='UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    event: Literal['website.published']
    userId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    websiteId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    slug: str = Field(
        ...,
        description='Subdomain slug: lowercase letters, digits and hyphens, a valid DNS label of at most 63 characters. Website Service doc.',
        pattern='^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$',
    )
    status: Literal['PUBLISHED']
    url: AnyUrl = Field(..., description='Absolute https URL.')


class WebsitePublishRequested(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    eventId: UUID = Field(..., description='Unique per emission (UUID).')
    occurredAt: AwareDatetime = Field(
        ..., description='UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    event: Literal['website.publish.requested']
    userId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    websiteId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    slug: str = Field(
        ...,
        description='Subdomain slug: lowercase letters, digits and hyphens, a valid DNS label of at most 63 characters. Website Service doc.',
        pattern='^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$',
    )


class WebsiteStatus(StrEnum):
    GENERATING = 'GENERATING'
    GENERATION_FAILED = 'GENERATION_FAILED'
    PREVIEW_READY = 'PREVIEW_READY'
    PUBLISHING = 'PUBLISHING'
    PUBLISH_FAILED = 'PUBLISH_FAILED'
    PUBLISHED = 'PUBLISHED'
    UNPUBLISHED = 'UNPUBLISHED'


class WorkExperience(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    company: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    position: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    description: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    startDate: str | None = Field(
        None,
        description='Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).',
        pattern='^[0-9]{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01]))?)?$',
    )
    endDate: str | None = Field(
        None,
        description='Date at the precision of the source: YYYY, YYYY-MM or YYYY-MM-DD. Never expanded with invented months or days (Communication Standards §3.4).',
        pattern='^[0-9]{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01]))?)?$',
    )
    isCurrent: bool | None = None


class CanonicalProfessionalProfile(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    fullName: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    headline: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    location: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    email: EmailStr | None = Field(None, description='Email address.')
    phone: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    links: list[Link] | None = Field(None, description='Professional URLs.')
    summary: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    workExperience: list[WorkExperience] | None = None
    education: list[Education] | None = None
    skills: list[Skill] | None = None
    projects: list[Project] | None = None
    certifications: list[Certification] | None = None
    languages: list[Language] | None = None
    volunteering: list[Volunteering] | None = None
    awards: list[Award] | None = None


class ContactSectionData(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    email: EmailStr | None = Field(None, description='Email address.')
    phone: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    links: list[LinkModel] | None = Field(None, min_length=1)


class CVExtractionResult(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    taskId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    sourceType: Literal['CV']
    profile: CanonicalProfessionalProfile


class HeroSectionData(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    title: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    subtitle: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    links: list[LinkModel] | None = None


class LinkedInExtractionResult(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    taskId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    sourceType: Literal['LINKEDIN']
    profile: CanonicalProfessionalProfile


class ProcessingCompleted(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    eventId: UUID = Field(..., description='Unique per emission (UUID).')
    occurredAt: AwareDatetime = Field(
        ..., description='UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    event: Literal['processing.completed']
    taskId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    sourceType: SourceType
    status: Literal['COMPLETED']
    resultS3Key: str = Field(
        ...,
        description='Object key relative to its bucket, for example user-123/job-456/cv.pdf. No leading slash.',
        max_length=1024,
        min_length=1,
        pattern='^[^/]',
    )
    attempt: int | None = Field(
        None,
        description='Retry attempt number (default 1). Request events may carry it; result and failure events echo it.',
        ge=1,
    )


class ProcessingFailed(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    eventId: UUID = Field(..., description='Unique per emission (UUID).')
    occurredAt: AwareDatetime = Field(
        ..., description='UTC RFC 3339 timestamp, for example 2026-11-17T14:30:00Z.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    event: Literal['processing.failed']
    taskId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    userId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    sourceType: SourceType
    stage: FailureStage
    errorCode: ErrorCode
    errorMessage: str = Field(
        ...,
        description='Short, safe to show to a user. No stack traces, CV text, personal data or secrets.',
        max_length=500,
        min_length=1,
    )
    retryable: bool = Field(
        ..., description='Whether the user can reasonably retry as is.'
    )
    attempts: int = Field(
        ..., description='Processing attempts made before giving up.', ge=1
    )
    diagnosticsS3Key: str | None = Field(
        None,
        description='Object key relative to its bucket, for example user-123/job-456/cv.pdf. No leading slash.',
        max_length=1024,
        min_length=1,
        pattern='^[^/]',
    )
    attempt: int | None = Field(
        None,
        description='Retry attempt number (default 1). Request events may carry it; result and failure events echo it.',
        ge=1,
    )


class Provenance(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    path: str = Field(
        ...,
        description='JSON Pointer into this document, for example /profile/skills/3. Updated if arrays are reordered.',
        pattern='^/profile(/[^/]+)*$',
    )
    sourceType: SourceType
    taskId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    reference: str | None = Field(
        None,
        description='Pointer into the source result or evidence, for example portfolio-api/Dockerfile.',
        min_length=1,
    )


class Repository(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str = Field(
        ...,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    url: AnyUrl = Field(..., description='Absolute https URL.')
    description: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    primaryLanguage: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )
    technologies: list[TechnologyModel] | None = None
    features: list[Feature] | None = None
    structure: list[StructureItem] | None = Field(
        None, description='Relevant files and directories.'
    )
    projectSummary: str | None = Field(
        None,
        description='Plain text (no HTML or Markdown; the renderer escapes everything).',
        min_length=1,
    )


class UnifiedProfile(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    sourceTypes: list[SourceType] = Field(
        ...,
        description='Sources that completed. The CV is required, so it is always present; a failed optional source is absent.',
        min_length=1,
    )
    profile: CanonicalProfessionalProfile
    provenance: list[Provenance] | None = None


class Sections1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(
        ...,
        description='Unique section id within the draft, for example hero.',
        pattern='^[a-z0-9][a-z0-9-]{0,63}$',
    )
    type: Literal['HERO']
    data: HeroSectionData


class Sections7(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(
        ...,
        description='Unique section id within the draft, for example hero.',
        pattern='^[a-z0-9][a-z0-9-]{0,63}$',
    )
    type: Literal['CONTACT']
    data: ContactSectionData


class Content(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    sections: list[
        Sections1
        | Sections2
        | Sections3
        | Sections4
        | Sections5
        | Sections6
        | Sections7
    ] = Field(
        ...,
        description='Ordered sections. Section ids must be unique within the draft (checked by the generator, not expressible in JSON Schema).',
        min_length=1,
    )


class WebsiteDraft(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    websiteId: str | None = Field(
        None,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    profileId: str | None = Field(
        None,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    templateId: str | None = Field(
        None,
        description='Readable template id, for example classic (Template System Spec §4).',
        pattern='^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$',
    )
    templateVersion: str | None = Field(
        None,
        description='Semantic version, for example 1.0.0.',
        pattern='^[0-9]+\\.[0-9]+\\.[0-9]+$',
    )
    status: WebsiteStatus | None = None
    content: Content


class GitHubAnalysisResult(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        regex_engine="python-re",
    )
    schemaVersion: Literal[1] = Field(
        ..., description='Major contract version. All MVP events use 1.'
    )
    jobId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    taskId: str = Field(
        ...,
        description='Opaque identifier. Never parse or derive meaning from it.',
        max_length=128,
        min_length=1,
    )
    sourceType: Literal['GITHUB']
    githubUsername: str = Field(
        ...,
        description='Normalized GitHub username (GitHub allows letters, digits and single hyphens, at most 39 characters).',
        pattern='^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$',
    )
    repositories: list[Repository]
