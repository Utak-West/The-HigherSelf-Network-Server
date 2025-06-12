#!/bin/bash
# Deployment script for The HigherSelf Network Server

# Exit on error
set -e

# Display help message
show_help() {
    echo "Usage: ./deploy.sh [OPTIONS]"
    echo "Deploy The HigherSelf Network Server"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV     Deployment environment (dev, staging, prod) [default: dev]"
    echo "  -b, --build       Build Docker images before deployment"
    echo "  -c, --clean       Clean up old containers and volumes"
    echo "  -h, --help        Display this help message"
    exit 0
}

# Default values
ENV="dev"
BUILD=false
CLEAN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -e|--env)
            ENV="$2"
            shift
            shift
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

# Validate environment
if [[ "$ENV" != "dev" && "$ENV" != "staging" && "$ENV" != "prod" ]]; then
    echo "Error: Invalid environment. Must be one of: dev, staging, prod"
    exit 1
fi

echo "Deploying The HigherSelf Network Server in $ENV environment..."

# Create required directories
mkdir -p logs data deployment/ssl

# Check if .env file exists, create from example if not
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Created .env file from template. Using test defaults for Devin deployment."
    else
        echo "Error: Neither .env nor .env.example found."
        exit 1
    fi
fi

# Clean up if requested
if [ "$CLEAN" = true ]; then
    echo "Cleaning up old containers and volumes..."
    docker-compose down -v
fi

# Build images if requested
if [ "$BUILD" = true ]; then
    echo "Building Docker images..."
    docker-compose build
fi

# Deploy based on environment
case $ENV in
    dev)
        echo "Starting development deployment..."
        if command -v "docker compose" &> /dev/null; then
            docker compose up -d
        else
            docker-compose up -d
        fi
        ;;
    staging)
        echo "Starting staging deployment..."
        if command -v "docker compose" &> /dev/null; then
            docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d
        else
            docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
        fi
        ;;
    prod)
        echo "Starting production deployment..."
        if command -v "docker compose" &> /dev/null; then
            docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        else
            docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        fi
        ;;
esac

echo "Deployment completed successfully!"
echo "API is available at http://localhost:8000"

# Wait for services to start and perform health check
echo "Waiting for services to start..."
sleep 30

echo "Performing health check..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Health check passed - API is responding"
else
    echo "⚠️  Health check failed - API may still be starting"
    echo "   Check logs with: docker-compose logs -f windsurf-agent"
fi

echo ""
echo "Useful commands:"
echo "  Check logs: docker-compose logs -f windsurf-agent"
echo "  Check status: docker-compose ps"
echo "  Health check: curl http://localhost:8000/health"
echo "  Stop services: docker-compose down"

exit 0
