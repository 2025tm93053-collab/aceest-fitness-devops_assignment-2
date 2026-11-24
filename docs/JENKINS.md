# Jenkins CI pipeline

## Why? (viva answer)
Jenkins is the automation server: every time code is pushed it checks the code out, lints, tests, analyses,
builds and publishes the image the same way each time, so a broken change is caught within minutes and
nothing is built by hand.

## Pipeline (`Jenkinsfile`, declarative)
| # | Stage | Real action | Fails the build when |
|---|---|---|---|
| 1 | Checkout | `checkout scm`, `git fetch --tags` | repo unreachable |
| 2 | Prepare | version from `git describe`, Docker check | Docker not running |
| 3 | Build test image | `docker build --target test` | build error |
| 4 | Lint | `flake8 .` in container | style/syntax errors |
| 5 | Unit tests + coverage | `pytest` in container; copies `coverage.xml`, `test-results.xml`; publishes JUnit | any test fails |
| 6 | SonarQube analysis | `sonar-scanner` (skippable with `RUN_SONAR`) | scanner error |
| 7 | Quality Gate | `waitForQualityGate abortPipeline: true` | gate = ERROR |
| 8 | Build runtime image | `docker build --target runtime` tagged with version | build error |
| 9 | Validate image | `scripts\validate-image.ps1`: healthy + non-root | unhealthy/root |
| 10 | Push to Docker Hub | login, push `<ver>` and `latest` (main branch only) | bad credentials |

Kubernetes deployment stages are added in the next phase.

## Install Jenkins on Windows
1. Install **JDK 17 or 21** and **Git for Windows**; install **Docker Desktop** (WSL2 backend) and start it.
2. Download the Jenkins LTS Windows installer from jenkins.io and run it. Default URL: `http://localhost:8080`.
3. **Important:** the Jenkins Windows service runs as *Local System* by default and cannot talk to Docker Desktop.
   `services.msc` -> *Jenkins* -> *Log On* -> *This account*: your own Windows user; restart the service.
   Your user must be allowed to use Docker (member of `docker-users`: `net localgroup docker-users <you> /add`, then sign out/in).
4. Unlock with the password in `C:\ProgramData\Jenkins\.jenkins\secrets\initialAdminPassword`, install suggested plugins, create the admin user.
5. Plugins: *Manage Jenkins -> Plugins*: **Git, Pipeline, Credentials Binding, JUnit, SonarQube Scanner** (usually pre-installed except Sonar).

## Credentials (never put secrets in the repo)
*Manage Jenkins -> Credentials -> System -> Global -> Add credentials*
| Kind | ID | Value |
|---|---|---|
| Username with password | `dockerhub-creds` | Docker Hub username + an **access token** (Docker Hub -> Account settings -> Personal access tokens, Read & Write) |
| Secret text | `sonar-token` | SonarQube token (see `docs/SONARQUBE.md`) |
| Username with password (only if the repo is private) | `github-pat` | GitHub username + personal access token |

The Jenkinsfile reads `dockerhub-creds` with `credentials()`; the password is masked in logs and is passed to
`docker login --password-stdin` so it never appears on a command line.

## Create the job
1. *New Item* -> name `aceest-fitness` -> **Pipeline** -> OK.
2. *Pipeline* section: Definition **Pipeline script from SCM**; SCM **Git**; Repository URL = **your GitHub repo URL**;
   Credentials = `github-pat` if private; Branch `*/main`; Script Path `Jenkinsfile`.
3. *Build Triggers*: the Jenkinsfile already declares `pollSCM('H/2 * * * *')`. Jenkins registers it **after the first build**, so click **Build Now** once.
   (Optional: also tick *Poll SCM* in the UI with the same schedule.)
4. First build: untick `RUN_SONAR` if SonarQube is not set up yet (*Build with Parameters*), then enable it later.

## SCM polling explained
Jenkins runs `git ls-remote` on the schedule. `H/2 * * * *` means "every 2 minutes at a hashed offset". If the branch
head changed since the last build, a build starts automatically; if not, nothing happens (the *Polling Log* in the job
shows each check). Polling is used instead of a GitHub webhook because a Jenkins on your laptop is not reachable from the internet.

Demonstrate it: edit any file, `git commit`, `git push`, then watch a new build appear within ~2 minutes (screenshot the build history).

## Evidence to capture
Stage View with all stages green; *Console Output* ending in `Finished: SUCCESS`; *Test Result* (JUnit) trend;
*Polling Log*; build history showing builds triggered by "SCM change"; Docker Hub tags page after a push.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `error during connect: ... pipe/docker_engine` | Jenkins service account cannot use Docker Desktop (install step 3) or Docker Desktop is stopped |
| `'git' is not recognized` / `'docker' is not recognized` | add to the system PATH, restart the Jenkins service |
| `No such tool: SonarScanner` / `No such server: SonarQube` | names in *Tools*/*System* must match exactly, case-sensitive |
| `Could not find credentials entry with ID 'dockerhub-creds'` | create it as *Global* with that exact ID |
| `denied: requested access to the resource is denied` on push | the credential must be a token with Write access; image repo name = `<dockerhub-user>/aceest-fitness` |
| Polling never triggers | run **Build Now** once; check *Polling Log*; confirm branch is `*/main` |
| `describe` gives only a hash | no tags fetched; push tags: `git push origin --tags` |
| Tests pass locally but fail in Jenkins | Jenkins runs the container build, not your venv: run `docker build --target test -t aceest-fitness:test .` then `docker run --rm aceest-fitness:test` locally |
| `RC` / `exit /b` weirdness in the test stage | the stage is `bat` (cmd); do not convert to `sh` on Windows agents |
