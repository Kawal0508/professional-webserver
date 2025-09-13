@echo off
REM Professional Web Server Deployment Script for Windows
REM This script handles deployment to various environments

setlocal enabledelayedexpansion

REM Configuration
set PROJECT_NAME=professional-webserver
set DOCKER_IMAGE=webserver
set DOCKER_TAG=latest
set CONTAINER_NAME=webserver

REM Functions
:log_info
echo [INFO] %~1
goto :eof

:log_success
echo [SUCCESS] %~1
goto :eof

:log_warning
echo [WARNING] %~1
goto :eof

:log_error
echo [ERROR] %~1
goto :eof

REM Check if command exists
:command_exists
where %1 >nul 2>&1
if %errorlevel%==0 (
    exit /b 0
) else (
    exit /b 1
)

REM Check prerequisites
:check_prerequisites
call :log_info "Checking prerequisites..."

call :command_exists docker
if %errorlevel% neq 0 (
    call :log_error "Docker is not installed. Please install Docker Desktop first."
    exit /b 1
)

call :command_exists docker-compose
if %errorlevel% neq 0 (
    call :log_error "Docker Compose is not installed. Please install Docker Desktop first."
    exit /b 1
)

call :log_success "Prerequisites check passed"
goto :eof

REM Build Docker image
:build_image
call :log_info "Building Docker image..."

docker build -t %DOCKER_IMAGE%:%DOCKER_TAG% .

if %errorlevel%==0 (
    call :log_success "Docker image built successfully"
) else (
    call :log_error "Failed to build Docker image"
    exit /b 1
)
goto :eof

REM Run tests
:run_tests
call :log_info "Running tests..."

REM Install test dependencies
pip install pytest pytest-cov requests

REM Run tests
python -m pytest test_webserver.py -v

if %errorlevel%==0 (
    call :log_success "All tests passed"
) else (
    call :log_error "Tests failed"
    exit /b 1
)
goto :eof

REM Deploy to development
:deploy_dev
call :log_info "Deploying to development environment..."

REM Create development config
(
echo version: '3.8'
echo services:
echo   webserver:
echo     build: .
echo     ports:
echo       - "8080:8080"
echo     volumes:
echo       - ./object_dir:/app/www:ro
echo       - ./logs:/app/logs
echo     environment:
echo       - SERVER_HOST=0.0.0.0
echo       - SERVER_PORT=8080
echo       - LOG_LEVEL=DEBUG
echo       - RATE_LIMIT=50
echo     restart: unless-stopped
) > docker-compose.dev.yml

REM Stop existing containers
docker-compose -f docker-compose.dev.yml down 2>nul

REM Start new containers
docker-compose -f docker-compose.dev.yml up -d

REM Wait for service to be ready
call :log_info "Waiting for service to be ready..."
timeout /t 10 /nobreak >nul

REM Health check
curl -f http://localhost:8080/health >nul 2>&1
if %errorlevel%==0 (
    call :log_success "Development deployment successful"
    call :log_info "Service available at: http://localhost:8080"
) else (
    call :log_error "Health check failed"
    exit /b 1
)
goto :eof

REM Run load test
:run_load_test
call :log_info "Running load test..."

REM Install load test dependencies
pip install requests

REM Run load test
python load_test.py http://localhost:8080 -t 20 -r 50

if %errorlevel%==0 (
    call :log_success "Load test completed"
) else (
    call :log_warning "Load test had issues"
)
goto :eof

REM Cleanup
:cleanup
call :log_info "Cleaning up..."

REM Remove unused Docker images
docker image prune -f

REM Remove unused containers
docker container prune -f

call :log_success "Cleanup completed"
goto :eof

REM Show usage
:show_usage
echo Usage: %0 [COMMAND]
echo.
echo Commands:
echo   build       Build Docker image
echo   test        Run tests
echo   dev         Deploy to development
echo   load-test   Run load test
echo   cleanup     Clean up unused Docker resources
echo   all         Build, test, and deploy to development
echo.
echo Examples:
echo   %0 build
echo   %0 dev
echo   %0 load-test
goto :eof

REM Main script
if "%1"=="build" (
    call :check_prerequisites
    call :build_image
) else if "%1"=="test" (
    call :run_tests
) else if "%1"=="dev" (
    call :check_prerequisites
    call :build_image
    call :deploy_dev
) else if "%1"=="load-test" (
    call :run_load_test
) else if "%1"=="cleanup" (
    call :cleanup
) else if "%1"=="all" (
    call :check_prerequisites
    call :build_image
    call :run_tests
    call :deploy_dev
    call :run_load_test
) else (
    call :show_usage
    exit /b 1
)

endlocal
