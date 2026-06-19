$ErrorActionPreference = "Stop"

try {
    docker info *> $null
    Write-Host "Docker is running. You can start DeepTutor with:"
    Write-Host "  docker compose -f docker-compose.deeptutor.yml up"
} catch {
    Write-Host "Docker is installed but the Docker daemon is not reachable." -ForegroundColor Yellow
    Write-Host "On Windows, start Docker Desktop and wait until it says 'Docker Desktop is running'."
    Write-Host "Then open a new PowerShell window and retry:"
    Write-Host "  docker compose -f docker-compose.deeptutor.yml up"
    Write-Host ""
    Write-Host "If Docker Desktop is not installed, install it first: https://www.docker.com/products/docker-desktop/"
    exit 1
}
