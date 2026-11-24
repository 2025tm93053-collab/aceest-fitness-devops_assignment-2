# Assignment Compliance / Evidence Matrix

| Requirement | Status | Evidence / next action |
|---|---|---|
| Web application / modular architecture | Implemented and reported validated | app source, test results |
| Git milestones/tags | Implemented | `git log`, `git tag` |
| Automated tests | Validated in sandbox | reported 77 passing; capture local run if possible |
| Coverage | Validated in sandbox | reported 99%; coverage report |
| Lint | Validated in sandbox | Flake8 clean |
| Dockerfile and image | Configured; build not executed | build/run locally, capture terminal |
| Jenkins CI | Configured; not executed | Jenkins job/build screenshot |
| SonarQube | Configured; not executed | analysis/quality gate screenshot |
| Docker registry publish | Configured/pending credentials and run | repository/image evidence |
| Kubernetes base manifests | Starter files provided; not validated | Minikube apply and status |
| Blue-Green | Starter/example only | live selector switch evidence |
| Canary | Starter/example only | ingress/controller validation |
| Shadow | app hook/config example only | mirrored traffic validation |
| A/B | starter/example only | routing validation |
| Rolling update / rollback | starter/example only | rollout and rollback output |

## Evidence checklist
- [ ] Dashboard/browser screenshot
- [ ] `pytest` output
- [ ] coverage report
- [ ] Flake8 output
- [ ] Docker build and run
- [ ] Docker health/version endpoint
- [ ] GitHub repository and tags
- [ ] Jenkins successful build
- [ ] SonarQube analysis and quality gate
- [ ] Kubernetes pods/services
- [ ] Strategy demonstration screenshots/output
