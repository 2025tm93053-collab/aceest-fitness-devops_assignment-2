// ACEest Fitness & Gym - declarative CI pipeline for a Windows-hosted Jenkins with Docker Desktop.
// Lint/tests run INSIDE the Docker "test" image, so the Jenkins agent needs no Python.
//
// Jenkins configuration this file expects (see docs/JENKINS.md):
//   Credentials : 'dockerhub-creds' (Username with password: Docker Hub user + access token)
//   Tools       : SonarQube Scanner installation named 'SonarScanner'
//   System      : SonarQube server named 'SonarQube' (holds the token credential)
//   Plugins     : Git, Pipeline, Credentials Binding, JUnit, SonarQube Scanner
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 40, unit: 'MINUTES')
    }

    // SCM polling: Jenkins asks Git every ~2 minutes (H = hashed minute to spread load).
    triggers { pollSCM('H/2 * * * *') }

    parameters {
        booleanParam(name: 'RUN_SONAR', defaultValue: true,
                     description: 'Run SonarQube analysis + quality gate (untick while setting Jenkins up)')
    }

    environment {
        IMAGE_NAME = 'aceest-fitness'
        // Creates DOCKERHUB_USR and DOCKERHUB_PSW; Jenkins masks both in the console log.
        DOCKERHUB  = credentials('dockerhub-creds')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                bat 'git fetch --tags --force'
            }
        }

        stage('Prepare') {
            steps {
                script {
                    // v3.0.0 -> 3.0.0 ; commits after a tag -> 3.0.0-4-gabc1234
                    def described = bat(returnStdout: true, script: '@git describe --tags --always').trim()
                    env.APP_VERSION = described.replaceFirst('^v', '')
                    env.IMAGE_REPO  = "${env.DOCKERHUB_USR}/${env.IMAGE_NAME}"
                    env.TEST_IMAGE  = "${env.IMAGE_NAME}:ci-${env.BUILD_NUMBER}"
                    currentBuild.displayName = "#${env.BUILD_NUMBER} ${env.APP_VERSION}"
                }
                bat 'docker version --format "client {{.Client.Version}} / server {{.Server.Version}}"'
            }
        }

        stage('Build test image') {
            steps {
                bat "docker build --target test -t ${env.TEST_IMAGE} ."
            }
        }

        stage('Lint (flake8)') {
            steps {
                bat "docker run --rm ${env.TEST_IMAGE} flake8 ."
            }
        }

        stage('Unit tests + coverage (pytest in container)') {
            steps {
                // Keep the exit code, copy the reports out, then fail the stage if tests failed.
                bat """
                    docker rm -f aceest-tests-${env.BUILD_NUMBER} 2>nul
                    docker run --name aceest-tests-${env.BUILD_NUMBER} ${env.TEST_IMAGE} pytest
                    set RC=%ERRORLEVEL%
                    docker cp aceest-tests-${env.BUILD_NUMBER}:/app/coverage.xml coverage.xml
                    docker cp aceest-tests-${env.BUILD_NUMBER}:/app/test-results.xml test-results.xml
                    docker rm -f aceest-tests-${env.BUILD_NUMBER}
                    exit /b %RC%
                """
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                    archiveArtifacts artifacts: 'coverage.xml,test-results.xml', allowEmptyArchive: true
                }
            }
        }

        stage('SonarQube analysis') {
            when { expression { params.RUN_SONAR } }
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'
                    withSonarQubeEnv('SonarQube') {   // injects SONAR_HOST_URL and the token
                        bat "\"${scannerHome}\\bin\\sonar-scanner.bat\" -Dsonar.projectVersion=${env.APP_VERSION}"
                    }
                }
            }
        }

        stage('Quality Gate') {
            when { expression { params.RUN_SONAR } }
            steps {
                // Needs the SonarQube -> Jenkins webhook (docs/SONARQUBE.md). Fails the build if the gate fails.
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build runtime image') {
            steps {
                bat "docker build --target runtime --build-arg APP_VERSION=${env.APP_VERSION} -t ${env.IMAGE_REPO}:${env.APP_VERSION} ."
            }
        }

        stage('Validate image') {
            steps {
                bat "powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\validate-image.ps1 -Image ${env.IMAGE_REPO}:${env.APP_VERSION}"
            }
        }

        stage('Push to Docker Hub') {
            when { expression { env.GIT_BRANCH in ['origin/main', 'main'] } }
            steps {
                // Single-quoted: Groovy does not interpolate the secret; cmd expands it, Jenkins masks it.
                bat '''
                    @echo off
                    echo %DOCKERHUB_PSW%| docker login -u %DOCKERHUB_USR% --password-stdin
                '''
                bat "docker push ${env.IMAGE_REPO}:${env.APP_VERSION}"
                bat "docker tag ${env.IMAGE_REPO}:${env.APP_VERSION} ${env.IMAGE_REPO}:latest"
                bat "docker push ${env.IMAGE_REPO}:latest"
            }
        }

        // Kubernetes deployment and release strategies are added in the next project phase.
    }

    post {
        always {
            bat(returnStatus: true, script: 'docker logout')
            bat(returnStatus: true, script: "docker rm -f aceest-tests-${env.BUILD_NUMBER} aceest-validate")
        }
        success { echo "Build ${env.APP_VERSION} succeeded" }
        failure { echo 'Build failed - see the first red stage above' }
    }
}
