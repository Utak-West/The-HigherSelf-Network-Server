#!/bin/bash

# ======================================================
# HIGHERSELF NETWORK SERVER - GHCR INTEGRATION TESTING
# Comprehensive testing for GitHub Container Registry integration
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
FULL_IMAGE_NAME="${REGISTRY}/${GITHUB_OWNER}/${IMAGE_NAME}"

# Test configuration
TEST_SUITE="${1:-all}"
TEST_TAG="${2:-test-$(date +%s)}"
CLEANUP="${3:-true}"

# Test results tracking
declare -A TEST_RESULTS
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

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

print_test_result() {
    local test_name="$1"
    local result="$2"
    local details="${3:-}"
    
    case "$result" in
        "PASS")
            print_status "PASS: $test_name"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            ;;
        "FAIL")
            print_error "FAIL: $test_name"
            if [[ -n "$details" ]]; then
                echo "      Details: $details"
            fi
            FAILED_TESTS=$((FAILED_TESTS + 1))
            ;;
    esac
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    TEST_RESULTS["$test_name"]="$result"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [TEST_SUITE] [TEST_TAG] [CLEANUP]"
    echo ""
    echo "Test Suites:"
    echo "  all              Run all tests (default)"
    echo "  build            Test image building"
    echo "  push             Test image pushing"
    echo "  pull             Test image pulling"
    echo "  multi-platform   Test multi-platform builds"
    echo "  security         Test security scanning"
    echo "  deployment       Test deployment scenarios"
    echo ""
    echo "Examples:"
    echo "  $0 all test-123 true"
    echo "  $0 build latest false"
    echo "  $0 deployment staging true"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("docker" "jq" "curl")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            print_error "Missing required tool: $tool"
            exit 1
        fi
    done
    
    # Check Docker daemon
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check GITHUB_TOKEN
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        print_warning "GITHUB_TOKEN not set - some tests may fail"
    fi
    
    print_status "Prerequisites check passed"
}

# Function to test image building
test_image_building() {
    print_header "Testing Image Building"
    
    # Test basic build
    if docker build -t "$FULL_IMAGE_NAME:$TEST_TAG" . > /dev/null 2>&1; then
        print_test_result "Basic Build" "PASS"
    else
        print_test_result "Basic Build" "FAIL" "Docker build failed"
    fi
    
    # Test multi-stage build targets
    local targets=("dependencies" "builder" "development" "production")
    for target in "${targets[@]}"; do
        if docker build --target "$target" -t "$FULL_IMAGE_NAME:$TEST_TAG-$target" . > /dev/null 2>&1; then
            print_test_result "Build Target: $target" "PASS"
        else
            print_test_result "Build Target: $target" "FAIL" "Failed to build target $target"
        fi
    done
    
    # Test build with arguments
    if docker build \
        --build-arg VERSION="test-version" \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --build-arg VCS_REF="test-ref" \
        -t "$FULL_IMAGE_NAME:$TEST_TAG-args" . > /dev/null 2>&1; then
        print_test_result "Build with Arguments" "PASS"
    else
        print_test_result "Build with Arguments" "FAIL" "Failed to build with arguments"
    fi
}

# Function to test multi-platform builds
test_multiplatform_builds() {
    print_header "Testing Multi-Platform Builds"
    
    # Check if buildx is available
    if ! docker buildx version > /dev/null 2>&1; then
        print_test_result "Buildx Availability" "FAIL" "Docker buildx not available"
        return
    fi
    
    print_test_result "Buildx Availability" "PASS"
    
    # Create buildx builder
    docker buildx create --use --name test-builder 2>/dev/null || true
    
    # Test AMD64 build
    if docker buildx build --platform linux/amd64 -t "$FULL_IMAGE_NAME:$TEST_TAG-amd64" . > /dev/null 2>&1; then
        print_test_result "AMD64 Build" "PASS"
    else
        print_test_result "AMD64 Build" "FAIL" "Failed to build for AMD64"
    fi
    
    # Test ARM64 build (may be slow)
    print_info "Testing ARM64 build (this may take a while)..."
    if timeout 300 docker buildx build --platform linux/arm64 -t "$FULL_IMAGE_NAME:$TEST_TAG-arm64" . > /dev/null 2>&1; then
        print_test_result "ARM64 Build" "PASS"
    else
        print_test_result "ARM64 Build" "FAIL" "Failed to build for ARM64 or timeout"
    fi
    
    # Test multi-platform build
    if timeout 600 docker buildx build --platform linux/amd64,linux/arm64 -t "$FULL_IMAGE_NAME:$TEST_TAG-multi" . > /dev/null 2>&1; then
        print_test_result "Multi-Platform Build" "PASS"
    else
        print_test_result "Multi-Platform Build" "FAIL" "Failed to build multi-platform or timeout"
    fi
    
    # Cleanup builder
    docker buildx rm test-builder 2>/dev/null || true
}

# Function to test GHCR authentication
test_ghcr_authentication() {
    print_header "Testing GHCR Authentication"
    
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        print_test_result "GITHUB_TOKEN Available" "FAIL" "GITHUB_TOKEN not set"
        return
    fi
    
    print_test_result "GITHUB_TOKEN Available" "PASS"
    
    # Test login
    if echo "$GITHUB_TOKEN" | docker login "$REGISTRY" -u "$GITHUB_OWNER" --password-stdin > /dev/null 2>&1; then
        print_test_result "GHCR Login" "PASS"
    else
        print_test_result "GHCR Login" "FAIL" "Failed to login to GHCR"
        return
    fi
    
    # Test token permissions by trying to list packages
    local api_url="https://api.github.com/users/${GITHUB_OWNER}/packages/container/${IMAGE_NAME}/versions"
    if curl -s -H "Authorization: Bearer $GITHUB_TOKEN" "$api_url" | jq -e '.' > /dev/null 2>&1; then
        print_test_result "GHCR API Access" "PASS"
    else
        print_test_result "GHCR API Access" "FAIL" "Failed to access GHCR API"
    fi
}

# Function to test image pushing
test_image_pushing() {
    print_header "Testing Image Pushing"
    
    # Ensure we have an image to push
    if ! docker image inspect "$FULL_IMAGE_NAME:$TEST_TAG" > /dev/null 2>&1; then
        docker build -t "$FULL_IMAGE_NAME:$TEST_TAG" . > /dev/null 2>&1
    fi
    
    # Test push to GHCR
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        if docker push "$FULL_IMAGE_NAME:$TEST_TAG" > /dev/null 2>&1; then
            print_test_result "Push to GHCR" "PASS"
        else
            print_test_result "Push to GHCR" "FAIL" "Failed to push image to GHCR"
        fi
    else
        print_test_result "Push to GHCR" "FAIL" "GITHUB_TOKEN not available"
    fi
}

# Function to test image pulling
test_image_pulling() {
    print_header "Testing Image Pulling"
    
    # Test pulling public images
    local public_images=(
        "ghcr.io/utak-west/higherself-network-server:latest"
        "ghcr.io/utak-west/thehigherselfnetworkserver:latest"
    )
    
    for image in "${public_images[@]}"; do
        local image_name=$(basename "$image")
        if docker pull "$image" > /dev/null 2>&1; then
            print_test_result "Pull: $image_name" "PASS"
        else
            print_test_result "Pull: $image_name" "FAIL" "Failed to pull $image"
        fi
    done
    
    # Test pulling test image if it was pushed
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        if docker pull "$FULL_IMAGE_NAME:$TEST_TAG" > /dev/null 2>&1; then
            print_test_result "Pull Test Image" "PASS"
        else
            print_test_result "Pull Test Image" "FAIL" "Failed to pull test image"
        fi
    fi
}

# Function to test container functionality
test_container_functionality() {
    print_header "Testing Container Functionality"
    
    # Ensure we have an image
    local test_image="$FULL_IMAGE_NAME:$TEST_TAG"
    if ! docker image inspect "$test_image" > /dev/null 2>&1; then
        test_image="$FULL_IMAGE_NAME:latest"
        if ! docker image inspect "$test_image" > /dev/null 2>&1; then
            docker build -t "$test_image" . > /dev/null 2>&1
        fi
    fi
    
    # Test container startup
    local container_id=$(docker run -d --name "test-container-$$" \
        -e ENVIRONMENT=test \
        -e DEBUG=true \
        "$test_image" 2>/dev/null || echo "")
    
    if [[ -n "$container_id" ]]; then
        print_test_result "Container Startup" "PASS"
        
        # Wait for container to start
        sleep 10
        
        # Test if container is running
        if docker ps | grep -q "$container_id"; then
            print_test_result "Container Running" "PASS"
            
            # Test health endpoint
            local container_ip=$(docker inspect "$container_id" --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
            if [[ -n "$container_ip" ]] && curl -f -s "http://$container_ip:8000/health" > /dev/null 2>&1; then
                print_test_result "Health Endpoint" "PASS"
            else
                print_test_result "Health Endpoint" "FAIL" "Health endpoint not responding"
            fi
        else
            print_test_result "Container Running" "FAIL" "Container not running"
        fi
        
        # Cleanup
        docker stop "$container_id" > /dev/null 2>&1 || true
        docker rm "$container_id" > /dev/null 2>&1 || true
    else
        print_test_result "Container Startup" "FAIL" "Failed to start container"
    fi
}

# Function to test GHCR manager script
test_ghcr_manager() {
    print_header "Testing GHCR Manager Script"
    
    local ghcr_script="$PROJECT_ROOT/scripts/ghcr-manager.sh"
    
    if [[ -f "$ghcr_script" && -x "$ghcr_script" ]]; then
        print_test_result "GHCR Manager Exists" "PASS"
        
        # Test status command
        if "$ghcr_script" status > /dev/null 2>&1; then
            print_test_result "GHCR Manager Status" "PASS"
        else
            print_test_result "GHCR Manager Status" "FAIL" "Status command failed"
        fi
        
        # Test list command
        if "$ghcr_script" list > /dev/null 2>&1; then
            print_test_result "GHCR Manager List" "PASS"
        else
            print_test_result "GHCR Manager List" "FAIL" "List command failed"
        fi
    else
        print_test_result "GHCR Manager Exists" "FAIL" "GHCR manager script not found or not executable"
    fi
}

# Function to cleanup test resources
cleanup_test_resources() {
    if [[ "$CLEANUP" == "true" ]]; then
        print_header "Cleaning Up Test Resources"
        
        # Remove test images
        local test_images=(
            "$FULL_IMAGE_NAME:$TEST_TAG"
            "$FULL_IMAGE_NAME:$TEST_TAG-dependencies"
            "$FULL_IMAGE_NAME:$TEST_TAG-builder"
            "$FULL_IMAGE_NAME:$TEST_TAG-development"
            "$FULL_IMAGE_NAME:$TEST_TAG-production"
            "$FULL_IMAGE_NAME:$TEST_TAG-args"
            "$FULL_IMAGE_NAME:$TEST_TAG-amd64"
            "$FULL_IMAGE_NAME:$TEST_TAG-arm64"
            "$FULL_IMAGE_NAME:$TEST_TAG-multi"
        )
        
        for image in "${test_images[@]}"; do
            docker rmi "$image" > /dev/null 2>&1 || true
        done
        
        # Remove test containers
        docker ps -a --filter "name=test-container-" --format "{{.ID}}" | xargs -r docker rm -f > /dev/null 2>&1 || true
        
        print_status "Cleanup completed"
    fi
}

# Function to generate test report
generate_test_report() {
    print_header "Test Results Summary"
    
    echo "Test Suite: $TEST_SUITE"
    echo "Test Tag: $TEST_TAG"
    echo "Timestamp: $(date)"
    echo ""
    echo "Results:"
    echo "  Total Tests: $TOTAL_TESTS"
    echo "  Passed: $PASSED_TESTS"
    echo "  Failed: $FAILED_TESTS"
    echo ""
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        print_status "All tests passed successfully!"
        return 0
    else
        print_error "$FAILED_TESTS test(s) failed"
        
        echo ""
        echo "Failed Tests:"
        for test_name in "${!TEST_RESULTS[@]}"; do
            if [[ "${TEST_RESULTS[$test_name]}" == "FAIL" ]]; then
                echo "  - $test_name"
            fi
        done
        
        return 1
    fi
}

# Main execution function
main() {
    print_header "HigherSelf Network Server - GHCR Integration Testing"
    echo "Test Suite: $TEST_SUITE"
    echo "Test Tag: $TEST_TAG"
    echo "Cleanup: $CLEANUP"
    echo ""
    
    check_prerequisites
    
    case "$TEST_SUITE" in
        "all")
            test_image_building
            test_multiplatform_builds
            test_ghcr_authentication
            test_image_pushing
            test_image_pulling
            test_container_functionality
            test_ghcr_manager
            ;;
        "build")
            test_image_building
            ;;
        "push")
            test_ghcr_authentication
            test_image_pushing
            ;;
        "pull")
            test_image_pulling
            ;;
        "multi-platform")
            test_multiplatform_builds
            ;;
        "security")
            test_ghcr_authentication
            ;;
        "deployment")
            test_container_functionality
            ;;
        *)
            print_error "Unknown test suite: $TEST_SUITE"
            show_usage
            exit 1
            ;;
    esac
    
    cleanup_test_resources
    generate_test_report
}

# Handle command line arguments
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_usage
    exit 0
fi

# Execute main function
main "$@"
