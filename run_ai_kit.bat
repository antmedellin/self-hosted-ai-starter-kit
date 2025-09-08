@echo off
REM Check if Docker is installed
where docker >nul 2>nul
IF ERRORLEVEL 1 (
    echo Docker is not installed. Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b
)

REM Check if Docker is running
docker info >nul 2>nul
IF ERRORLEVEL 1 (
    echo Docker is not running. Please start Docker Desktop.
    pause
    exit /b
)

REM Clone the repo if it doesn't exist
IF NOT EXIST "self-hosted-ai-starter-kit" (
    git clone https://github.com/antmedellin/self-hosted-ai-starter-kit.git
)
cd self-hosted-ai-starter-kit

REM Copy .env.example to .env if .env does not exist
IF NOT EXIST ".env" (
    copy .env.example .env
    echo Please update your .env file with secrets and passwords!
    pause
)

REM Pull latest images
docker compose  pull

REM Build local images
docker compose  build

REM Run Docker Compose with CPU profile
docker compose up -d

REM Wait for n8n to start (adjust time as needed)
timeout /t 15

REM Open n8n home page in default browser
start http://localhost:5678

pause