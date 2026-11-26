"""Idempotent init job: creates private buckets and checks every queue exists.

Queues themselves are declared in elasticmq.conf, so ElasticMQ creates them on
start; this job only verifies them, so a typo in the config fails `up` early.
"""

from __future__ import annotations

import sys

from botocore.exceptions import ClientError

from stack import QUEUES, buckets, s3, sqs, wait_for


def ensure_bucket(client, name: str) -> None:
    try:
        client.head_bucket(Bucket=name)
        print(f"  bucket {name}: exists")
    except ClientError:
        client.create_bucket(Bucket=name)
        print(f"  bucket {name}: created")
    # Private: remove any anonymous bucket policy. New buckets are private by default.
    try:
        client.delete_bucket_policy(Bucket=name)
    except ClientError:
        pass


def main() -> int:
    sqs_client = sqs()
    s3_client = s3()

    print("Waiting for ElasticMQ and S3 (RustFS)...")
    wait_for("ElasticMQ", sqs_client.list_queues)
    wait_for("S3 (RustFS)", s3_client.list_buckets)

    print("Buckets:")
    for name in buckets():
        ensure_bucket(s3_client, name)

    print("Queues:")
    missing = []
    for queue in QUEUES:
        for name in (queue.name, queue.dlq):
            try:
                sqs_client.get_queue_url(QueueName=name)
                print(f"  queue {name}: ok")
            except ClientError:
                missing.append(name)
                print(f"  queue {name}: MISSING")
    if missing:
        print(f"Missing queues {missing}: check infra/compose/elasticmq/elasticmq.conf", file=sys.stderr)
        return 1
    print("Init done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
