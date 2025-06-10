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

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create one based on .env.example"
    exit 1
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
        docker-compose up -d
        ;;
    staging)
        echo "Starting staging deployment..."
        docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
        ;;
    prod)
        echo "Starting production deployment..."
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        ;;
esac

echo "Deployment completed successfully!"
echo "API is available at http://localhost:8000"
echo "To check logs: docker-compose logs -f windsurf-agent"
echo "To check health: curl http://localhost:8000/health"

exit 0
