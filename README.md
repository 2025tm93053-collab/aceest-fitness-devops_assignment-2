# ACEest Fitness — DevOps Assignment 2

## Overview
ACEest Fitness is a Flask web application for fitness-coach client management, programmes, workout/progress tracking and reports. This project converts the legacy desktop-oriented fitness workflow into a modular web application and provides DevOps configuration for testing, containerisation, CI and quality analysis.

## Architecture
- Flask application factory and blueprints (`system`, `auth`, `clients`, `tracking`)
- Service layer for validation, programme logic, membership and chart rendering
- SQLite persistence via repository/data-access modules
- Jinja templates and CSS UI
- Pytest suite; Flake8; coverage
- Docker multi-stage configuration; Jenkins pipeline; SonarQube properties

## Features
- Authentication with password hashing, CSRF protection and role checks
- Client CRUD and tracking, programme and PDF/CSV features as implemented
- Health and version endpoints; environment-configurable deployment variants
- Shadow mode write protection hook

## Local setup (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
pytest
flake8 .
$env:ADMIN_USERNAME='admin'; $env:ADMIN_PASSWORD='ChangeMe123!'
flask --app wsgi create-user
python -m flask --app wsgi run
```
Use a unique strong password; do not commit secrets. See `docs/DOCKER.md`, `docs/JENKINS.md`, `docs/SONARQUBE.md`.

## DevOps status
The application/tests and lint were reported validated (77 tests, 99% coverage, clean Flake8, Gunicorn smoke test). Docker build, Jenkins execution and SonarQube analysis remain unexecuted in the original sandbox; configure and validate on your machine. Kubernetes manifests are provided as starter configurations and require deployment validation.

## Version history
See `docs/VERSIONS.md`. Tags `v1.0.0`, `v2.0.0`, `v3.0.0` represent milestones.
