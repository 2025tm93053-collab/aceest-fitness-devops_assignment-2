# Project checklist

Legend - **IMPLEMENTED**: files written. **VALIDATED**: actually executed, result stated.
**NOT YET EXECUTED**: written but not run. **REQUIRES YOUR CONFIGURATION**: needs your accounts/tools.

## Phase status
| # | Item | Implemented | Validated | Evidence / note |
|---|---|---|---|---|
| 1 | Flask app (factory, blueprints, services, SQLite, auth, roles, CSRF, reports) | yes | yes | 77 tests pass, 99% coverage, flake8 clean, Gunicorn smoke test |
| 2 | Git history + tags v1.0.0 / v2.0.0 / v3.0.0 | yes | yes | each snapshot tested before commit: 31 / 51 / 77 passing; v3 tree identical to validated app |
| 3 | `docs/VERSIONS.md` (provenance + tag->image mapping) | yes | n/a | |
| 4 | Dockerfile + .dockerignore | yes | **partly** | `docker build` could NOT run here (Docker Hub blocked in sandbox). Simulated stage-by-stage instead: see below |
| 5 | Test stage commands (`flake8 && pytest`, bare `pytest`) | yes | yes (simulated) | found + fixed `pythonpath` bug this way |
| 6 | Runtime stage: Gunicorn CMD, non-root, `/health`, persistence on a data dir, PDF | yes | yes (simulated) | ran as uid 65534 with exact CMD; client survived restart |
| 7 | `docker build` / `docker run` of the real image | yes | **NOT YET EXECUTED** | run on your machine: `docs/DOCKER.md` |
| 8 | `scripts/validate-image.ps1` | yes | **NOT YET EXECUTED** | no PowerShell here |
| 9 | Jenkinsfile (10 stages, SCM polling, credentials, Windows `bat`) | yes | **NOT YET EXECUTED** | only a bracket/structure check was possible; no Jenkins or Groovy here. REQUIRES YOUR CONFIGURATION |
| 10 | `sonar-project.properties`, Sonar docs, quality gate stage | yes | **NOT YET EXECUTED** | coverage.xml verified to contain `app/...` paths; no SonarQube run. REQUIRES YOUR CONFIGURATION |
| 11 | Docker Hub push | yes (in Jenkinsfile + docs) | NOT YET EXECUTED | REQUIRES YOUR CONFIGURATION (account + token) |
| 12 | GitHub remote | no | no | REQUIRES YOUR CONFIGURATION: create repo, `git remote add`, push |
| 13 | Kubernetes / Minikube + 5 strategies | no | no | starts after Docker, Jenkins, SonarQube work on your machine |
| 14 | README, 2-3 page report, evidence list, compliance matrix | no | no | final phases |

## Test log (this environment)
| Command | Result |
|---|---|
| `python -m pytest` on v1.0.0 / v2.0.0 / v3.0.0 | 31 / 51 / 77 passed |
| `flake8 .` | clean |
| clean-venv copy of the Docker build context: `flake8 . && pytest` | 77 passed, 99% coverage |
| gunicorn as non-root with `DATABASE_PATH` on a data dir | `/health` 200; login, create client, restart, client still present; PDF 200 |
| `docker build` | blocked: sandbox proxy denies Docker Hub, so the base image cannot be pulled |
