<#
 Smoke-test a built runtime image: start it, wait for the Docker HEALTHCHECK
 (GET /health), confirm it does not run as root, then remove the container.
 Usage:  .\scripts\validate-image.ps1 -Image <dockerhub-user>/aceest-fitness:3.0.0
#>
param(
    [Parameter(Mandatory = $true)][string]$Image,
    [string]$Name = "aceest-validate",
    [int]$TimeoutSec = 60
)
$ErrorActionPreference = "Continue"
docker rm -f $Name *> $null
docker run -d --name $Name -e SECRET_KEY=validate $Image | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "docker run failed"; exit 1 }
$exitCode = 0
try {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $status = ""
    while ((Get-Date) -lt $deadline) {
        $status = (docker inspect --format "{{.State.Health.Status}}" $Name).Trim()
        if ($status -eq "healthy" -or $status -eq "unhealthy") { break }
        Start-Sleep -Seconds 2
    }
    if ($status -ne "healthy") {
        docker logs $Name
        throw "Container is not healthy (status: $status)"
    }
    $json = docker exec $Name python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/health').read().decode())"
    Write-Host "GET /health -> $json"
    $uid = (docker exec $Name id -u).Trim()
    if ($uid -eq "0") { throw "Container runs as root" }
    Write-Host "Container runs as non-root uid $uid"
    Write-Host "IMAGE VALIDATION PASSED"
}
catch {
    Write-Host "IMAGE VALIDATION FAILED: $_"
    $exitCode = 1
}
finally {
    docker rm -f $Name *> $null
}
exit $exitCode
