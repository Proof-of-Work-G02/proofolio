# CI workflows (KAN-9)

One workflow per check. The job named like the workflow (`contracts`, `backend-ci`, ...) is the
status check to require on `main`.

| Check | Runs its real work when these change | What it does today |
| --- | --- | --- |
| `branch-name` | every PR | `<frontend\|backend\|ai>/feature/<name>` (AGENTS.md) |
| `pr-title` | every PR, also when the title is edited | `type(scope): text (KAN-9)`, keys `FE-` `BE-` `AI-` `KAN-` (AGENTS.md) |
| `security` | every PR and push to `main` | gitleaks on the new commits, `npm audit` and `pip-audit` on every lockfile / requirements file |
| `contracts` | `contracts/**`, `scripts/dev.py`, `Makefile` | `make contracts-setup contracts-check contracts-breaking` |
| `compose-smoke` | `infra/compose/**`, `scripts/dev.py`, `Makefile`, `.env.example`, migrations | `make up smoke` |
| `frontend-ci` | `apps/frontend/**`, `packages/**`, `services/render-worker/**`, `contracts/**` | placeholder until FE-21 |
| `backend-ci` | `services/core-backend/**`, `services/website-service/**`, `contracts/**` | Core Backend lint, type checks and tests |
| `ai-ci` | the three AI services, `services/_shared/**`, `contracts/**` | placeholder until AI-7 |
| `renderer-parity` | `packages/**`, `services/render-worker/**`, `services/website-service/**` | placeholder until FE-33 |
| `terraform` | `infra/terraform/**` | placeholder until KAN-10 |
| `nightly` | 02:00 UTC and on demand | placeholders for KAN-11 (end-to-end) and AI-17 (real model) |

Each workflow also re-runs its real work when its own `.yml` file changes.

## How the path filter works

```
changes  ->  <name> (run)  ->  <name>
(which paths    (the real work,   (always runs: passes when the work
 changed?)       or skipped)       passed or was skipped, fails otherwise)
```

GitHub's own `on: pull_request: paths:` filter is not used on purpose: a workflow skipped that way
never reports, so a required check would wait forever. Here the last job always reports.

## Replacing a placeholder

Edit the `run` job of your workflow (keep the `changes` job and the final job as they are), and
add the same commands to `python scripts/dev.py test` so they also run locally.

## Run it locally

```sh
python scripts/dev.py contracts-setup   # once
python scripts/dev.py test              # contracts-check + contracts-breaking
python scripts/dev.py up                # then
python scripts/dev.py smoke             # the compose-smoke check
```
