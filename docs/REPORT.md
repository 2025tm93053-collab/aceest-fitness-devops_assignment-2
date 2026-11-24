# ACEest Fitness — Introduction to DevOps Assignment 2

## 1. Introduction and objective
ACEest Fitness is a fitness-coaching application for maintaining client profiles, programme information and workout/progress data. The objective of this assignment is to modernise the application as a web-based system and demonstrate software delivery practices including automated testing, container packaging, pipeline automation and quality analysis configuration.

## 2. Application and architecture
The application is implemented using Flask. An application factory supports configuration and registration of blueprints for system endpoints, authentication, clients and tracking. Business logic is organised into services and database operations into a repository/data-access layer. SQLite provides persistence. The user interface is delivered through Jinja templates and static CSS. Authentication uses password hashing; the implementation includes CSRF protection, validation and role-based restrictions. `/health` and `/version` provide operational endpoints. Deployment hooks expose colour/variant information and shadow mode can disable writes.

Legacy functionality was consolidated from supplied desktop versions, including workout/diet content, programme selection/generation, client and progress data, metrics, membership information, exports and reporting. Desktop-specific interactions were replaced with web workflows.

## 3. Testing and quality
The reported validation of the final application includes 77 Pytest tests passing, 99% coverage and clean Flake8 output. Gunicorn smoke testing reportedly verified `/health` and `/version`, login, dashboard/client-list responses and persistence/report behaviour. These results were obtained in the source-development sandbox and are not evidence of a Docker/Jenkins/Kubernetes deployment on the submitter's machine. The Docker image build, Jenkins pipeline execution and SonarQube analysis are pending local validation.

## 4. DevOps implementation
Docker configuration includes test and runtime stages, a Gunicorn runtime, non-root execution and configurable settings. Jenkinsfile stages are intended to automate checkout, lint, tests, coverage, image build and optional quality/publishing activities. SonarQube configuration supports source and coverage analysis and quality-gate integration. The Docker build was not executed in the original sandbox because access to the base-image registry was blocked. Jenkins and SonarQube were configured in files but not executed.

## 5. Deployment strategy extension and status
Kubernetes starter manifests are included for a deployment and service, with strategy examples for blue-green selector switching, canary routing, shadow mirroring, A/B routing and rolling-update/rollback concepts. These are configuration examples, not validated live deployments. A Minikube environment, container image and ingress controller would be required to demonstrate them. SQLite is not appropriate for unrestricted multi-replica shared writes; demonstrations should use isolated/read-only replicas or a suitable shared database.

## 6. Conclusion
The application and automated test suite provide a foundation for DevOps delivery. The repository contains configuration and documentation for containerisation, CI and code-quality automation, while local execution and deployment evidence remain to be collected. All execution claims should be supported by actual console output and screenshots.
