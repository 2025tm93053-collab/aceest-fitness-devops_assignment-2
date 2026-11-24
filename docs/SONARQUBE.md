# SonarQube

## Why? (viva answer)
SonarQube is static analysis: it reads the source without running it and reports bugs, vulnerabilities,
security hot-spots, code smells, duplication and (with `coverage.xml`) test coverage. The **quality gate**
is a pass/fail rule set; if it fails, the Jenkins pipeline stops, so low-quality code never gets built into an image.

## Files
* `sonar-project.properties` - project key `aceest-fitness`, sources `app`, tests `tests`, Python 3.12, coverage report `coverage.xml`.
* `coverage.xml` - produced by `pytest` (config in `pytest.ini` / `.coveragerc`, `relative_files = True` so paths read `app/db.py`).
* `Jenkinsfile` - stages *SonarQube analysis* and *Quality Gate*.

## One-time server setup (Windows, Docker Desktop)
```powershell
docker volume create sonarqube-data
docker run -d --name sonarqube -p 9000:9000 -v sonarqube-data:/opt/sonarqube/data sonarqube:community
# (if that tag is not found, pick the current Community tag at https://hub.docker.com/_/sonarqube)
Start-Process http://localhost:9000      # first start takes 1-2 minutes; login admin / admin, then change the password
```
1. **Token**: avatar -> *My Account* -> *Security* -> *Generate Tokens* (type *User token*). Copy it once; it is never shown again.
2. **Project**: *Create project* -> *Manually* -> key `aceest-fitness`, name `ACEest Fitness & Gym`.
3. **Quality gate**: *Quality Gates* -> default **Sonar way** is fine (new code: no new bugs/vulnerabilities, coverage >= 80%, duplication <= 3%, hotspots reviewed). Document any change you make.

## Run an analysis locally (no Jenkins), PowerShell
```powershell
# 1) produce coverage.xml (needs the dev dependencies in a venv, or use the Docker test image)
python -m pip install -r requirements-dev.txt
python -m pytest                                   # writes coverage.xml + test-results.xml

# 2) scan using the official scanner container (nothing to install)
$env:SONAR_TOKEN = "<paste token>"
docker run --rm -e SONAR_HOST_URL="http://host.docker.internal:9000" -e SONAR_TOKEN=$env:SONAR_TOKEN `
  -v "${PWD}:/usr/src" sonarsource/sonar-scanner-cli

# 3) open http://localhost:9000/dashboard?id=aceest-fitness  and screenshot Overview + Quality Gate status
```

## Jenkins integration
1. *Manage Jenkins -> Plugins*: install **SonarQube Scanner**.
2. *Manage Jenkins -> Credentials -> Global -> Add*: kind **Secret text**, ID `sonar-token`, value = the token.
3. *Manage Jenkins -> System -> SonarQube servers -> Add*: name **SonarQube**, URL `http://localhost:9000`
   (use the host IP if Jenkins runs in a container), token credential `sonar-token`, tick *Environment variables*.
4. *Manage Jenkins -> Tools -> SonarQube Scanner installations -> Add*: name **SonarScanner**, *Install automatically*.
5. **Webhook** (needed for the quality gate): SonarQube -> *Administration -> Configuration -> Webhooks -> Create*:
   name `jenkins`, URL `http://<jenkins-host>:8080/sonarqube-webhook/` (trailing slash required). If SonarQube runs in
   Docker and Jenkins on Windows, use `http://host.docker.internal:8080/sonarqube-webhook/`.

The pipeline then runs `sonar-scanner` inside `withSonarQubeEnv('SonarQube')` and `waitForQualityGate abortPipeline: true`.

## Capturing evidence
Screenshot: project *Overview* (bugs, vulnerabilities, smells, coverage, duplication), the *Quality Gate: Passed/Failed*
badge, and the Jenkins stage view showing both Sonar stages. Optionally export the report from *Project -> Activity*.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `Not authorized` | token wrong/expired; regenerate and update the Jenkins credential |
| Quality Gate stage hangs until timeout | webhook missing or Jenkins URL unreachable from the SonarQube container |
| Coverage shows 0% | `coverage.xml` missing in workspace, or paths do not start with `app/` (re-run pytest; do not move the file) |
| `host.docker.internal` unresolved | Docker Desktop only; otherwise use the host's LAN IP |
| SonarQube container exits | Docker Desktop memory < 4 GB; raise it in *Settings -> Resources* |
