# Contributing

1. Pick the first unblocked task in your Jira space (rank order).
2. Branch from `main` using the branch name written on the task: `frontend/feature/<name>`, `backend/feature/<name>` or `ai/feature/<name>`.
3. Build against `contracts/`; mock anything not ready.
4. Open a pull request titled in Conventional Commits style with the Jira key, e.g. `feat(core): add job upload endpoint (BE-11)`.
5. Tick the acceptance criteria in the PR template. Squash merge after approval and green checks.

Rules: no direct pushes to `main`; no secrets in the repo; contract changes go in their own PR and need approval from all three teams.
