#!/bin/bash

# HigherSelf Network Server - Docker Setup Guide
# Complete setup script for Docker container deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 HigherSelf Network Server - Docker Setup${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if Docker is installed and running
echo -e "${BLUE}Checking Docker installation...${NC}"

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

print_status "Docker is installed and running"
echo "Docker version: $(docker --version)"
echo ""

# Check if .env file exists
echo -e "${BLUE}Checking environment configuration...${NC}"

if [[ ! -f ".env" ]]; then
    print_warning ".env file not found"
    
    if [[ -f "terraform/.env.example" ]]; then
        print_info "Creating .env file from template..."
        cp terraform/.env.example .env
        print_status ".env file created from template"
        print_warning "Please edit .env file with your actual values before proceeding"
    else
        print_error "No .env template found"
        echo "Please create a .env file with your configuration"
        exit 1
    fi
else
    print_status ".env file found"
fi

# Create required directories
echo -e "${BLUE}Creating required directories...${NC}"

REQUIRED_DIRS=(
    "logs"
    "logs/mongodb"
    "data"
    "deployment/ssl"
    "deployment/mongodb"
    "deployment/redis"
    "deployment/prometheus"
    "deployment/grafana/provisioning"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        print_status "Created directory: $dir"
    else
        print_status "Directory exists: $dir"
    fi
done

# Check configuration files
echo ""
echo -e "${BLUE}Checking configuration files...${NC}"

CONFIG_FILES=(
    "deployment/nginx.conf"
    "deployment/redis/redis.conf"
    "deployment/prometheus/prometheus.yml"
)

for file in "${CONFIG_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        print_status "Configuration file exists: $file"
    else
        print_warning "Configuration file missing: $file"
    fi
done

# Build the Docker image
echo ""
echo -e "${BLUE}Building HigherSelf Network Server Docker image...${NC}"

if docker build -t thehigherselfnetworkserver .; then
    print_status "Docker image built successfully"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Show next steps
echo ""
echo -e "${GREEN}🎉 Docker setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1. ${YELLOW}Configure your .env file:${NC}"
echo "   Edit .env with your actual API tokens and passwords"
echo ""
echo "2. ${YELLOW}Start the services:${NC}"
echo "   ${GREEN}docker-compose up -d${NC}"
echo ""
echo "3. ${YELLOW}Check service status:${NC}"
echo "   ${GREEN}docker-compose ps${NC}"
echo ""
echo "4. ${YELLOW}View logs:${NC}"
echo "   ${GREEN}docker-compose logs -f windsurf-agent${NC}"
echo ""
echo "5. ${YELLOW}Access your services:${NC}"
echo "   • Main Application: http://localhost:8000"
echo "   • Health Check: http://localhost:8000/health"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Prometheus: http://localhost:9090"
echo "   • Grafana: http://localhost:3000"
echo "   • Consul: http://localhost:8500"
echo ""

# Environment-specific notes
echo -e "${BLUE}Important Notes:${NC}"
echo "• Make sure to configure your integration tokens in .env"
echo "• MongoDB and Redis will use default passwords (change for production)"
echo "• SSL is disabled by default (enable for production)"
echo "• All data is persisted in Docker volumes"
echo ""

echo -e "${GREEN}Ready to deploy your HigherSelf Network Server!${NC}"
