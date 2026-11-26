# Proofolio

AI platform that builds and hosts personal portfolio websites from a CV plus optional GitHub and LinkedIn data.
Published sites live at `username.ourdomain.com`.

Design: see the Confluence pages "System Architecture – Happy Flow" and "Task Planning and Delivery Plan".
Run the local stack: `python scripts/dev.py up` then `python scripts/dev.py smoke` (needs Docker; see `infra/README.md`).

Work is tracked in Jira (spaces FE, BE, AI, KAN). Read `docs/CONTRIBUTING.md` before your first pull request.

| Folder | Owner |
|---|---|
| `apps/frontend`, `packages/*`, `services/render-worker` | Frontend |
| `services/core-backend`, `services/website-service`, `infra/` | Backend |
| `services/cv-extraction`, `services/linkedin-extraction`, `services/github-analysis`, `services/_shared/python` | AI |
| `contracts/` | All three teams (every team must approve) |
