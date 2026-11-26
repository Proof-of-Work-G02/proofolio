# infra

Owner: Backend team.

| Folder | What it is |
|---|---|
| `compose/` | Local development stack (KAN-8): Postgres, SQS (ElasticMQ), S3 (RustFS) |
| `terraform/` | AWS environment (KAN-10). Not started: AWS is on hold for now |

## Local stack

Needs Docker Desktop and Python 3.10+. No AWS account, no API keys.

```sh
python scripts/dev.py up      # start everything, create buckets, run migrations
python scripts/dev.py smoke   # prove every queue, DLQ and bucket works
python scripts/dev.py down    # stop (data is kept)
python scripts/dev.py reset   # stop, delete all data, start again
```

On Linux/macOS `make up`, `make smoke`, `make down`, `make reset` do the same.
Configuration comes from `.env` if it exists, otherwise `.env.example`
(copy it: `cp .env.example .env`).

| What | From your machine | From a container in Compose |
|---|---|---|
| Postgres | `localhost:5432`, db/user/password `proofolio` | `postgres:5432` |
| SQS API | `http://localhost:9324` | `http://elasticmq:9324` |
| S3 API | `http://localhost:9000` | `http://s3:9000` |
| S3 web console | `http://localhost:9001/rustfs/console/index.html` (`proofolio` / `proofolio-secret`) | |

The Compose project is called `proofolio-dev`, so `down` and `reset` never touch
other Compose projects on the same machine.

### Queues

Six queues, each with its own dead-letter queue (DLQ). A message that is received
`maxReceiveCount` times without being deleted moves to the DLQ. Numbers come from
`docs/Design/Failure Handling Design.md` §4.2 and live in
`compose/elasticmq/elasticmq.conf` (and `compose/tools/stack.py`, which the smoke
test checks against the running server).

| Queue | DLQ | Visibility timeout | maxReceiveCount | Producer → consumer |
|---|---|---|---|---|
| `cv-extraction` | `cv-extraction-dlq` | 5 min | 3 | Core → CV Extraction |
| `github-analysis` | `github-analysis-dlq` | 10 min | 3 | Core → GitHub Analysis |
| `linkedin-extraction` | `linkedin-extraction-dlq` | 5 min | 3 | Core → LinkedIn Extraction |
| `website-generation` | `website-generation-dlq` | 10 min | 3 | Core → Website Service |
| `website-publishing` | `website-publishing-dlq` | 10 min | 3 | Website Service outbox → Website Publisher |
| `processing-results` | `processing-results-dlq` | 1 min | 5 | AI services and Website Service → Core |

DLQs keep messages 14 days; source queues keep the SQS default of 4 days.

### Buckets

All private (anonymous reads return 403).

| Bucket | Holds |
|---|---|
| `portfolio-uploads` | Uploaded CVs and LinkedIn PDFs |
| `extraction-results` | JSON results of the AI services |
| `published-websites` | Rendered static sites |

### Database migrations

`python scripts/dev.py migrate` (also run by `up`) runs Alembic in
`services/core-backend` first, then `services/website-service`, when those folders
have an `alembic.ini` (BE-8 adds them). Core goes first because `websites` has
foreign keys to Core tables. Install the service's dependencies (including
`alembic`) in the Python you run the script with.

### Adding your service

`compose/docker-compose.yml` has a commented block per service. Uncomment yours once
it has a Dockerfile, and use the in-network hosts from the table above
(`postgres`, `elasticmq`, `s3`), not `localhost`.

### Why RustFS and not MinIO

The design docs say MinIO. MinIO stopped publishing Docker images in 2025, so the
stack uses [RustFS](https://github.com/rustfs/rustfs) (Apache-2.0), which speaks the
same S3 API on the same ports. Code only sees an S3 endpoint URL, so nothing else
changes, and on AWS it is real S3.

### Troubleshooting

| Symptom | Fix |
|---|---|
| `Docker is installed but not running` | Start Docker Desktop |
| `port is already allocated` | Something else uses 5432/9000/9001/9324: change `POSTGRES_PORT`, `S3_PORT`, ... in `.env` |
| Smoke: `queue is not empty` | The DLQ check needs empty queues: `python scripts/dev.py reset` |
| Want to look at queues or files | Queues: `aws --endpoint-url http://localhost:9324 sqs list-queues` (any credentials); files: the S3 console (link above) |
