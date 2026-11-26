# GENERATED FILE - DO NOT EDIT.
# Source: contracts/schemas. Regenerate with `make contracts-types`
# (or `npm run types` in contracts/tooling).

from __future__ import annotations

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import AnyUrl, AwareDatetime, BaseModel, ConfigDict, Field


class ProofolioContracts(BaseModel):
    pass


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


class SourceType(StrEnum):
    CV = 'CV'
    GITHUB = 'GITHUB'
    LINKEDIN = 'LINKEDIN'


class TaskStatus(StrEnum):
    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


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
