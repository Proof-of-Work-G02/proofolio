from typing import Annotated, Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

NonEmptyString = Annotated[str, Field(min_length=1)]
NonEmptySecret = Annotated[SecretStr, Field(min_length=1)]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(hide_input_in_errors=True, env_ignore_empty=True)

    database_url: PostgresDsn
    aws_endpoint_url_s3: AnyHttpUrl | None = None
    s3_bucket_uploads: NonEmptyString
    s3_bucket_extraction_results: NonEmptyString
    s3_bucket_published_websites: NonEmptyString
    aws_endpoint_url_sqs: AnyHttpUrl | None = None
    sqs_queue_url_cv_extraction: AnyHttpUrl
    sqs_queue_url_github_analysis: AnyHttpUrl
    sqs_queue_url_linkedin_extraction: AnyHttpUrl
    sqs_queue_url_website_generation: AnyHttpUrl
    sqs_queue_url_website_publishing: AnyHttpUrl
    sqs_queue_url_processing_results: AnyHttpUrl
    sqs_dlq_url_cv_extraction: AnyHttpUrl
    sqs_dlq_url_github_analysis: AnyHttpUrl
    sqs_dlq_url_linkedin_extraction: AnyHttpUrl
    sqs_dlq_url_website_generation: AnyHttpUrl
    sqs_dlq_url_website_publishing: AnyHttpUrl
    sqs_dlq_url_processing_results: AnyHttpUrl
    frontend_url: AnyHttpUrl
    session_secret: NonEmptySecret
    internal_service_secret: NonEmptySecret
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("frontend_url")
    @classmethod
    def validate_frontend_origin(cls, url: AnyHttpUrl) -> AnyHttpUrl:
        if url.path != "/" or url.query or url.fragment or url.username or url.password:
            raise ValueError("FRONTEND_URL must be an HTTP origin")
        return url
