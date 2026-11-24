# Docker

## Why containers? (viva answer)
The image packages the app, Python and every dependency, so it behaves the same on a laptop, on
Jenkins and in Kubernetes ("works on my machine" disappears). Images are immutable and versioned,
which makes releases and rollbacks a matter of choosing a tag.

## What the Dockerfile does
| Stage | Purpose |
|---|---|
| `base` | `python:3.12-slim` + production requirements only |
| `test` | adds flake8/pytest + the whole source; `CMD` = `flake8 . && pytest`. Used by Jenkins so tests run **inside the container** (assignment task 7) |
| `runtime` | only `app/` + `wsgi.py`; non-root user (uid 10001); Gunicorn; `HEALTHCHECK` on `/health` |

Design choices:
* **Gunicorn, not `flask run`** - the Flask dev server is single-purpose and not hardened; Gunicorn is a production WSGI server (process management, timeouts, logging).
* **1 worker + 4 threads** - SQLite allows one writer at a time, so extra worker processes only add lock contention.
* **Non-root** - a compromised app cannot write to the image or act as root.
* **Persistent data** - SQLite lives in `/data` (`DATABASE_PATH=/data/aceest.db`), declared as a volume. Without a volume the data disappears with the container.
* **No secrets in the image** - `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` are supplied at run time.

Environment variables: `SECRET_KEY`, `DATABASE_PATH`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `APP_VERSION`,
`DEPLOY_COLOR`, `VARIANT`, `SHADOW_MODE`, `PORT`.

## Commands (Windows PowerShell, working directory = repository root)

```powershell
# 1. Build + run lint and the 77 tests inside the container
docker build --target test -t aceest-fitness:test .
docker run --rm aceest-fitness:test
#    expected: "77 passed" and coverage ~99%

# 2. Build the runtime image (replace 3.0.0 with the version you are building)
docker build --target runtime --build-arg APP_VERSION=3.0.0 -t aceest-fitness:3.0.0 .

# 3. Run with a named volume for persistent SQLite data
docker volume create aceest-data
docker run -d --name aceest -p 8000:8000 -v aceest-data:/data `
  -e SECRET_KEY="change-me-to-a-long-random-string" `
  -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD="choose-a-password" `
  aceest-fitness:3.0.0

# 4. Check it
Invoke-RestMethod http://localhost:8000/health        # status ok, version 3.0.0
docker ps                                              # STATUS shows (healthy) after ~15 s
Start-Process http://localhost:8000                    # log in with the admin credentials above

# 5. Prove persistence: remove the container, start a new one on the same volume
docker rm -f aceest
docker run -d --name aceest -p 8000:8000 -v aceest-data:/data -e SECRET_KEY=x aceest-fitness:3.0.0
#    your clients are still there

# 6. Automated smoke test used by Jenkins
.\scripts\validate-image.ps1 -Image aceest-fitness:3.0.0

# 7. Tag and push to Docker Hub (replace <dockerhub-user>)
docker login
docker tag aceest-fitness:3.0.0 <dockerhub-user>/aceest-fitness:3.0.0
docker push <dockerhub-user>/aceest-fitness:3.0.0
docker tag aceest-fitness:3.0.0 <dockerhub-user>/aceest-fitness:latest
docker push <dockerhub-user>/aceest-fitness:latest

# 8. Pull on another machine
docker pull <dockerhub-user>/aceest-fitness:3.0.0
```

Podman users: replace `docker` with `podman` (assignment allows either).

## Troubleshooting
| Symptom | Cause / fix |
|---|---|
| `error during connect ... docker_engine` | Docker Desktop is not running - start it and wait for "Engine running" |
| Container exits immediately | `docker logs aceest`; usually a bad env var |
| `(unhealthy)` | `docker logs aceest`; check the port is 8000 inside the container |
| Data lost after `docker rm` | you ran without `-v aceest-data:/data` |
| Logged out after each restart | no fixed `SECRET_KEY` was supplied (a random one is generated at start) |
| `permission denied` on `/data` with a bind mount | use a named volume instead of a Windows folder |
