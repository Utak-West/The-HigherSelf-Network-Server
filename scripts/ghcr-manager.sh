#!/bin/bash

# ======================================================
# HIGHERSELF NETWORK SERVER - GITHUB CONTAINER REGISTRY MANAGER
# Comprehensive GHCR integration and container management
# ======================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# GHCR configuration
REGISTRY="ghcr.io"
GITHUB_OWNER="${GITHUB_REPOSITORY_OWNER:-utak-west}"
IMAGE_NAME="higherself-network-server"
BASE_IMAGE_NAME="thehigherselfnetworkserver"
FULL_IMAGE_NAME="${REGISTRY}/${GITHUB_OWNER}/${IMAGE_NAME}"
BASE_FULL_IMAGE_NAME="${REGISTRY}/${GITHUB_OWNER}/${BASE_IMAGE_NAME}"

# Environment configuration
ENVIRONMENT="${ENVIRONMENT:-development}"
ACTION="${1:-status}"
TAG="${2:-latest}"
PLATFORM="${3:-linux/amd64,linux/arm64}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "======================================================="
    echo "$1"
    echo "======================================================="
    echo -e "${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [ACTION] [TAG] [PLATFORM]"
    echo ""
    echo "Actions:"
    echo "  status           Show GHCR status and available images"
    echo "  login            Login to GitHub Container Registry"
    echo "  build            Build and push image to GHCR"
    echo "  pull             Pull image from GHCR"
    echo "  push             Push existing image to GHCR"
    echo "  list             List all available tags"
    echo "  inspect          Inspect image metadata"
    echo "  cleanup          Clean up old images"
    echo "  test             Test image functionality"
    echo "  deploy           Deploy image to environment"
    echo ""
    echo "Tags:"
    echo "  latest           Latest stable version (default)"
    echo "  main             Main branch build"
    echo "  v1.0.0           Specific version tag"
    echo "  sha-abc123       Commit-specific build"
    echo ""
    echo "Platforms:"
    echo "  linux/amd64,linux/arm64    Multi-platform (default)"
    echo "  linux/amd64                AMD64 only"
    echo "  linux/arm64                ARM64 only"
    echo ""
    echo "Environment Variables:"
    echo "  GITHUB_TOKEN               GitHub token for authentication"
    echo "  GITHUB_REPOSITORY_OWNER    GitHub repository owner"
    echo "  ENVIRONMENT                Target environment"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 build v1.0.0"
    echo "  $0 pull latest"
    echo "  $0 deploy production"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check required tools
    local required_tools=("docker" "jq" "curl")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "Missing required tools:"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Function to login to GHCR
login_to_ghcr() {
    print_header "Logging in to GitHub Container Registry"
    
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        print_error "GITHUB_TOKEN environment variable is required"
        print_info "Set GITHUB_TOKEN with a personal access token that has 'write:packages' scope"
        exit 1
    fi
    
    echo "$GITHUB_TOKEN" | docker login "$REGISTRY" -u "$GITHUB_OWNER" --password-stdin
    
    print_status "Successfully logged in to GHCR"
}

# Function to show GHCR status
show_ghcr_status() {
    print_header "GitHub Container Registry Status"
    
    echo "Registry: $REGISTRY"
    echo "Owner: $GITHUB_OWNER"
    echo "Image Name: $IMAGE_NAME"
    echo "Full Image: $FULL_IMAGE_NAME"
    echo "Base Image: $BASE_FULL_IMAGE_IMAGE_NAME"
    echo ""
    
    # Check if logged in
    if docker system info | grep -q "Username: $GITHUB_OWNER"; then
        print_status "Logged in to GHCR"
    else
        print_warning "Not logged in to GHCR"
        print_info "Run: $0 login"
    fi
    
    # List available tags
    print_info "Available tags:"
    list_available_tags
}

# Function to list available tags
list_available_tags() {
    local api_url="https://api.github.com/users/${GITHUB_OWNER}/packages/container/${IMAGE_NAME}/versions"
    
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        local response=$(curl -s -H "Authorization: Bearer $GITHUB_TOKEN" "$api_url")
    else
        local response=$(curl -s "$api_url")
    fi
    
    if echo "$response" | jq -e '.message' > /dev/null 2>&1; then
        local error_message=$(echo "$response" | jq -r '.message')
        print_warning "API Error: $error_message"
        return 1
    fi
    
    if echo "$response" | jq -e '.[0]' > /dev/null 2>&1; then
        echo "$response" | jq -r '.[].metadata.container.tags[]?' | head -20 | while read -r tag; do
            if [[ -n "$tag" && "$tag" != "null" ]]; then
                echo "  - $tag"
            fi
        done
    else
        print_warning "No tags found or package not accessible"
    fi
}

# Function to build and push image
build_and_push() {
    print_header "Building and Pushing Image to GHCR"
    
    local tag="$1"
    local platforms="$2"
    
    # Ensure logged in
    if ! docker system info | grep -q "Username: $GITHUB_OWNER"; then
        login_to_ghcr
    fi
    
    # Get version information
    local version=$(git describe --tags --always --dirty 2>/dev/null || echo "dev")
    local commit_sha=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    local build_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    print_info "Building image with tag: $tag"
    print_info "Platforms: $platforms"
    print_info "Version: $version"
    
    # Build and push with buildx
    docker buildx create --use --name higherself-builder 2>/dev/null || true
    
    docker buildx build \
        --platform "$platforms" \
        --tag "$FULL_IMAGE_NAME:$tag" \
        --tag "$FULL_IMAGE_NAME:latest" \
        --tag "$BASE_FULL_IMAGE_NAME:$tag" \
        --tag "$BASE_FULL_IMAGE_NAME:latest" \
        --label "org.opencontainers.image.title=HigherSelf Network Server" \
        --label "org.opencontainers.image.description=Enterprise automation platform for multi-business entity management" \
        --label "org.opencontainers.image.vendor=HigherSelf Network" \
        --label "org.opencontainers.image.version=$version" \
        --label "org.opencontainers.image.created=$build_date" \
        --label "org.opencontainers.image.revision=$commit_sha" \
        --label "org.opencontainers.image.source=https://github.com/${GITHUB_OWNER}/The-HigherSelf-Network-Server" \
        --label "org.opencontainers.image.documentation=https://github.com/${GITHUB_OWNER}/The-HigherSelf-Network-Server/blob/main/docs/README.md" \
        --label "org.opencontainers.image.licenses=MIT" \
        --label "com.higherself.version=$version" \
        --label "com.higherself.build-date=$build_date" \
        --label "com.higherself.vcs-ref=$commit_sha" \
        --label "com.higherself.business-entities=the_7_space,am_consulting,higherself_core" \
        --build-arg VERSION="$version" \
        --build-arg BUILD_DATE="$build_date" \
        --build-arg VCS_REF="$commit_sha" \
        --push \
        .
    
    print_status "Image built and pushed successfully"
    print_info "Available at: $FULL_IMAGE_NAME:$tag"
}

# Function to pull image
pull_image() {
    local tag="$1"
    
    print_header "Pulling Image from GHCR"
    print_info "Pulling: $FULL_IMAGE_NAME:$tag"
    
    docker pull "$FULL_IMAGE_NAME:$tag"
    
    print_status "Image pulled successfully"
}

# Function to inspect image
inspect_image() {
    local tag="$1"
    
    print_header "Inspecting Image: $FULL_IMAGE_NAME:$tag"
    
    # Check if image exists locally
    if ! docker image inspect "$FULL_IMAGE_NAME:$tag" > /dev/null 2>&1; then
        print_info "Image not found locally, pulling..."
        pull_image "$tag"
    fi
    
    # Show image details
    echo "Image Details:"
    docker image inspect "$FULL_IMAGE_NAME:$tag" | jq -r '.[0] | {
        Id: .Id,
        Created: .Created,
        Size: .Size,
        Architecture: .Architecture,
        Os: .Os,
        Labels: .Config.Labels
    }'
    
    echo ""
    echo "Image Layers:"
    docker history "$FULL_IMAGE_NAME:$tag" --format "table {{.CreatedBy}}\t{{.Size}}" | head -10
    
    echo ""
    echo "Security Scan:"
    docker scout quickview "$FULL_IMAGE_NAME:$tag" 2>/dev/null || echo "Docker Scout not available"
}

# Function to test image
test_image() {
    local tag="$1"
    
    print_header "Testing Image: $FULL_IMAGE_NAME:$tag"
    
    # Check if image exists locally
    if ! docker image inspect "$FULL_IMAGE_NAME:$tag" > /dev/null 2>&1; then
        print_info "Image not found locally, pulling..."
        pull_image "$tag"
    fi
    
    # Test container startup
    print_info "Testing container startup..."
    local container_id=$(docker run -d --name "test-higherself-$$" \
        -e ENVIRONMENT=test \
        -e DEBUG=true \
        "$FULL_IMAGE_NAME:$tag")
    
    # Wait for container to start
    sleep 10
    
    # Check if container is running
    if docker ps | grep -q "$container_id"; then
        print_status "Container started successfully"
        
        # Test health endpoint
        local container_ip=$(docker inspect "$container_id" --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
        if [[ -n "$container_ip" ]]; then
            if curl -f -s "http://$container_ip:8000/health" > /dev/null 2>&1; then
                print_status "Health endpoint responding"
            else
                print_warning "Health endpoint not responding"
            fi
        fi
    else
        print_error "Container failed to start"
        docker logs "$container_id"
    fi
    
    # Cleanup
    docker stop "$container_id" > /dev/null 2>&1 || true
    docker rm "$container_id" > /dev/null 2>&1 || true
    
    print_status "Image test completed"
}

# Function to cleanup old images
cleanup_images() {
    print_header "Cleaning up Old Images"
    
    # Remove old local images
    print_info "Removing old local images..."
    docker image prune -f
    
    # Remove untagged images
    local untagged_images=$(docker images --filter "dangling=true" -q)
    if [[ -n "$untagged_images" ]]; then
        docker rmi $untagged_images
        print_status "Removed untagged images"
    fi
    
    # List remaining images
    print_info "Remaining HigherSelf images:"
    docker images | grep -E "(higherself|thehigherselfnetworkserver)" || echo "No HigherSelf images found"
}

# Function to deploy image
deploy_image() {
    local environment="$1"
    local tag="${2:-latest}"
    
    print_header "Deploying Image to $environment"
    
    # Update environment configuration
    export ENVIRONMENT="$environment"
    export DOCKER_IMAGE_TAG="$tag"
    
    # Use the docker-terragrunt-deploy script
    if [[ -f "$PROJECT_ROOT/scripts/docker-terragrunt-deploy.sh" ]]; then
        "$PROJECT_ROOT/scripts/docker-terragrunt-deploy.sh" "$environment" deploy containers
    else
        print_warning "docker-terragrunt-deploy.sh not found, using docker-compose"
        
        # Update docker-compose to use GHCR image
        cd "$PROJECT_ROOT"
        DOCKER_IMAGE="$FULL_IMAGE_NAME:$tag" docker-compose up -d
    fi
    
    print_status "Deployment completed"
}

# Main execution function
main() {
    print_header "HigherSelf Network Server - GHCR Manager"
    echo "Registry: $REGISTRY"
    echo "Image: $FULL_IMAGE_NAME"
    echo "Action: $ACTION"
    echo "Tag: $TAG"
    echo ""
    
    check_prerequisites
    
    case "$ACTION" in
        "status")
            show_ghcr_status
            ;;
        "login")
            login_to_ghcr
            ;;
        "build")
            build_and_push "$TAG" "$PLATFORM"
            ;;
        "pull")
            pull_image "$TAG"
            ;;
        "push")
            print_error "Push action requires build - use 'build' action instead"
            exit 1
            ;;
        "list")
            list_available_tags
            ;;
        "inspect")
            inspect_image "$TAG"
            ;;
        "cleanup")
            cleanup_images
            ;;
        "test")
            test_image "$TAG"
            ;;
        "deploy")
            deploy_image "$TAG" "${3:-latest}"
            ;;
        "-h"|"--help"|"help")
            show_usage
            ;;
        *)
            print_error "Unknown action: $ACTION"
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
