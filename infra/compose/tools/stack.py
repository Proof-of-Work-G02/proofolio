"""Single list of the local queues and buckets, shared by init.py and smoke.py.

The numbers mirror infra/compose/elasticmq/elasticmq.conf and
docs/Design/Failure Handling Design.md §4.2. smoke.py fails if the running
ElasticMQ disagrees with this table, so the two cannot drift apart silently.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

import boto3
from botocore.config import Config


@dataclass(frozen=True)
class Queue:
    name: str
    visibility_timeout_s: int
    max_receive_count: int

    @property
    def dlq(self) -> str:
        return f"{self.name}-dlq"


QUEUES: tuple[Queue, ...] = (
    Queue("cv-extraction", 300, 3),
    Queue("github-analysis", 600, 3),
    Queue("linkedin-extraction", 300, 3),
    Queue("website-generation", 600, 3),
    Queue("website-publishing", 600, 3),
    Queue("processing-results", 60, 5),
)

BUCKET_ENV_VARS = ("S3_BUCKET_UPLOADS", "S3_BUCKET_EXTRACTION_RESULTS", "S3_BUCKET_PUBLISHED_WEBSITES")
DEFAULT_BUCKETS = ("portfolio-uploads", "extraction-results", "published-websites")


def buckets() -> list[str]:
    return [os.environ.get(var) or default for var, default in zip(BUCKET_ENV_VARS, DEFAULT_BUCKETS)]


def _client(service: str, endpoint_var: str):
    return boto3.client(
        service,
        endpoint_url=os.environ[endpoint_var],
        region_name=os.environ.get("AWS_REGION", "eu-central-1"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "local"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "local"),
        config=Config(retries={"max_attempts": 2}, s3={"addressing_style": "path"}),
    )


def sqs():
    return _client("sqs", "AWS_ENDPOINT_URL_SQS")


def s3():
    # S3 (RustFS) credentials are separate from the dummy SQS ones.
    return boto3.client(
        "s3",
        endpoint_url=os.environ["AWS_ENDPOINT_URL_S3"],
        region_name=os.environ.get("AWS_REGION", "eu-central-1"),
        aws_access_key_id=os.environ.get("S3_ACCESS_KEY_ID", "proofolio"),
        aws_secret_access_key=os.environ.get("S3_SECRET_ACCESS_KEY", "proofolio-secret"),
        config=Config(retries={"max_attempts": 2}, s3={"addressing_style": "path"}),
    )


T = TypeVar("T")


def wait_for(what: str, fn: Callable[[], T], timeout_s: float = 60) -> T:
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - any failure means "not ready yet"
            if time.monotonic() > deadline:
                raise RuntimeError(f"{what} not ready after {timeout_s:.0f}s: {exc}") from exc
            time.sleep(1)
