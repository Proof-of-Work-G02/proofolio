"""Smoke test for the local stack (KAN-8).

Checks:
  * Postgres accepts connections.
  * Every queue has the expected visibility timeout, DLQ and maxReceiveCount.
  * One message round-trips through every queue.
  * A message received maxReceiveCount times without being deleted lands in the DLQ.
  * One object round-trips through every bucket, and anonymous reads are refused.

The DLQ check needs empty queues (it would otherwise bump the receive count of
other messages), so run it on a fresh stack: `python scripts/dev.py reset`.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

import psycopg

from stack import QUEUES, Queue, buckets, s3, sqs, wait_for

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail and not ok else ''}")
    if not ok:
        failures.append(name)


def receive_marker(client, url: str, marker: str, visibility_timeout: int | None, wait_s: int = 5):
    kwargs = {"QueueUrl": url, "MaxNumberOfMessages": 10, "WaitTimeSeconds": 1}
    if visibility_timeout is not None:
        kwargs["VisibilityTimeout"] = visibility_timeout
    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        for message in client.receive_message(**kwargs).get("Messages", []):
            if marker in message["Body"]:
                return message
    return None


def check_postgres() -> None:
    print("Postgres:")
    try:
        with wait_for("Postgres", lambda: psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3)) as conn:
            check("select 1", conn.execute("select 1").fetchone() == (1,))
    except Exception as exc:  # noqa: BLE001
        check("connect", False, str(exc))


def check_queue(client, queue: Queue) -> None:
    url = client.get_queue_url(QueueName=queue.name)["QueueUrl"]
    dlq_url = client.get_queue_url(QueueName=queue.dlq)["QueueUrl"]
    attrs = client.get_queue_attributes(QueueUrl=url, AttributeNames=["All"])["Attributes"]
    redrive = json.loads(attrs.get("RedrivePolicy", "{}"))

    check(f"{queue.name}: visibility {queue.visibility_timeout_s}s",
          int(attrs["VisibilityTimeout"]) == queue.visibility_timeout_s, f"got {attrs['VisibilityTimeout']}")
    check(f"{queue.name}: DLQ {queue.dlq}", str(redrive.get("deadLetterTargetArn", "")).endswith(":" + queue.dlq),
          f"got {redrive}")
    check(f"{queue.name}: maxReceiveCount {queue.max_receive_count}",
          int(redrive.get("maxReceiveCount", -1)) == queue.max_receive_count, f"got {redrive}")

    # Round trip.
    marker = f"smoke-{uuid.uuid4()}"
    client.send_message(QueueUrl=url, MessageBody=json.dumps({"smoke": marker}))
    message = receive_marker(client, url, marker, visibility_timeout=None)
    check(f"{queue.name}: send and receive", message is not None)
    if message:
        client.delete_message(QueueUrl=url, ReceiptHandle=message["ReceiptHandle"])

    # DLQ: receive maxReceiveCount times without deleting; the next receive moves it.
    if int(attrs.get("ApproximateNumberOfMessages", "0")) or int(attrs.get("ApproximateNumberOfMessagesNotVisible", "0")):
        check(f"{queue.name}: moves to DLQ after {queue.max_receive_count} failed receives", False,
              "queue is not empty; run `python scripts/dev.py reset` first")
        return
    marker = f"smoke-dlq-{uuid.uuid4()}"
    client.send_message(QueueUrl=url, MessageBody=json.dumps({"smoke": marker}))
    received = 0
    for _ in range(queue.max_receive_count):
        if receive_marker(client, url, marker, visibility_timeout=0):
            received += 1
    leftover = receive_marker(client, url, marker, visibility_timeout=0, wait_s=2)
    dead = receive_marker(client, dlq_url, marker, visibility_timeout=None)
    check(f"{queue.name}: moves to DLQ after {queue.max_receive_count} failed receives",
          received == queue.max_receive_count and leftover is None and dead is not None,
          f"received={received} leftover={leftover is not None} in_dlq={dead is not None}")
    if dead:
        client.delete_message(QueueUrl=dlq_url, ReceiptHandle=dead["ReceiptHandle"])
    if leftover:
        client.delete_message(QueueUrl=url, ReceiptHandle=leftover["ReceiptHandle"])


def check_bucket(client, bucket: str) -> None:
    key = f"smoke/{uuid.uuid4()}.txt"
    body = b"proofolio smoke test"
    client.put_object(Bucket=bucket, Key=key, Body=body)
    got = client.get_object(Bucket=bucket, Key=key)["Body"].read()
    check(f"{bucket}: put and get", got == body)

    public_url = f"{os.environ['AWS_ENDPOINT_URL_S3'].rstrip('/')}/{bucket}/{key}"
    try:
        urllib.request.urlopen(public_url, timeout=5)
        status = 200
    except urllib.error.HTTPError as exc:
        status = exc.code
    check(f"{bucket}: anonymous read refused", status == 403, f"got HTTP {status}")
    client.delete_object(Bucket=bucket, Key=key)


def main() -> int:
    check_postgres()

    print("Queues:")
    sqs_client = sqs()
    for queue in QUEUES:
        check_queue(sqs_client, queue)

    print("Buckets:")
    s3_client = s3()
    for bucket in buckets():
        check_bucket(s3_client, bucket)

    if failures:
        print(f"\nSmoke test FAILED ({len(failures)} checks).", file=sys.stderr)
        return 1
    print("\nSmoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
