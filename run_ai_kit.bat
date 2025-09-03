@echo off
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

REM Run Docker Compose with CPU profile
docker compose --profile cpu up -d

pause