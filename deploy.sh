#!/bin/bash

# Professional Web Server Deployment Script
# This script handles deployment to various environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="professional-webserver"
DOCKER_IMAGE="webserver"
DOCKER_TAG="latest"
CONTAINER_NAME="webserver"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command_exists docker; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
    
    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Run tests
run_tests() {
    log_info "Running tests..."
    
    # Install test dependencies
    pip install pytest pytest-cov requests
    
    # Run tests
    python -m pytest test_webserver.py -v
    
    if [ $? -eq 0 ]; then
        log_success "All tests passed"
    else
        log_error "Tests failed"
        exit 1
    fi
}

# Deploy to development
deploy_dev() {
    log_info "Deploying to development environment..."
    
    # Create development config
    cat > docker-compose.dev.yml << EOF
version: '3.8'
services:
  webserver:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./object_dir:/app/www:ro
      - ./logs:/app/logs
    environment:
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8080
      - LOG_LEVEL=DEBUG
      - RATE_LIMIT=50
    restart: unless-stopped
EOF
    
    # Stop existing containers
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    
    # Start new containers
    docker-compose -f docker-compose.dev.yml up -d
    
    # Wait for service to be ready
    log_info "Waiting for service to be ready..."
    sleep 10
    
    # Health check
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        log_success "Development deployment successful"
        log_info "Service available at: http://localhost:8080"
    else
        log_error "Health check failed"
        exit 1
    fi
}

# Deploy to production
deploy_prod() {
    log_info "Deploying to production environment..."
    
    # Create production config
    cat > docker-compose.prod.yml << EOF
version: '3.8'
services:
  webserver:
    image: ${DOCKER_IMAGE}:${DOCKER_TAG}
    ports:
      - "8080:8080"
    volumes:
      - /var/www/html:/app/www:ro
      - /var/log/webserver:/app/logs
    environment:
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8080
      - LOG_LEVEL=INFO
      - RATE_LIMIT=100
    restart: always
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/ssl/certs:/etc/nginx/ssl:ro
    depends_on:
      - webserver
    restart: always
EOF
    
    # Stop existing containers
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    # Start new containers
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for service to be ready
    log_info "Waiting for service to be ready..."
    sleep 15
    
    # Health check
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        log_success "Production deployment successful"
        log_info "Service available at: http://localhost"
    else
        log_error "Health check failed"
        exit 1
    fi
}

# Run load test
run_load_test() {
    log_info "Running load test..."
    
    # Install load test dependencies
    pip install requests
    
    # Run load test
    python load_test.py http://localhost:8080 -t 20 -r 50
    
    if [ $? -eq 0 ]; then
        log_success "Load test completed"
    else
        log_warning "Load test had issues"
    fi
}

# Cleanup
cleanup() {
    log_info "Cleaning up..."
    
    # Remove unused Docker images
    docker image prune -f
    
    # Remove unused containers
    docker container prune -f
    
    log_success "Cleanup completed"
}

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build       Build Docker image"
    echo "  test        Run tests"
    echo "  dev         Deploy to development"
    echo "  prod        Deploy to production"
    echo "  load-test   Run load test"
    echo "  cleanup     Clean up unused Docker resources"
    echo "  all         Build, test, and deploy to development"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 dev"
    echo "  $0 prod"
    echo "  $0 load-test"
}

# Main script
main() {
    case "${1:-}" in
        "build")
            check_prerequisites
            build_image
            ;;
        "test")
            run_tests
            ;;
        "dev")
            check_prerequisites
            build_image
            deploy_dev
            ;;
        "prod")
            check_prerequisites
            build_image
            deploy_prod
            ;;
        "load-test")
            run_load_test
            ;;
        "cleanup")
            cleanup
            ;;
        "all")
            check_prerequisites
            build_image
            run_tests
            deploy_dev
            run_load_test
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
