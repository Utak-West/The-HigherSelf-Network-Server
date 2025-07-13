#!/bin/bash
# Higher Self Network Server - Docker Entrypoint Script
# Addresses critical issues: Environment loading, Redis connection, service health checks

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Function to load environment variables
load_environment() {
    log "Loading environment configuration..."
    
    # Load environment file based on ENVIRONMENT variable
    ENV_FILE=".env"
    if [ "$ENVIRONMENT" = "production" ]; then
        ENV_FILE=".env.production"
    elif [ "$ENVIRONMENT" = "staging" ]; then
        ENV_FILE=".env.staging"
    elif [ "$ENVIRONMENT" = "development" ]; then
        ENV_FILE=".env.development"
    fi
    
    # Load environment file if it exists
    if [ -f "$ENV_FILE" ]; then
        log "Loading environment from $ENV_FILE"
        export $(grep -v '^#' "$ENV_FILE" | xargs)
        success "Environment variables loaded from $ENV_FILE"
    else
        warning "Environment file $ENV_FILE not found, using container environment variables"
    fi
    
    # Validate critical environment variables
    validate_environment
}

# Function to validate critical environment variables
validate_environment() {
    log "Validating critical environment variables..."
    
    local missing_vars=()
    
    # Check Redis configuration
    if [ -z "$REDIS_URI" ]; then
        missing_vars+=("REDIS_URI")
    fi
    
    # Check Notion configuration
    if [ -z "$NOTION_API_TOKEN" ]; then
        missing_vars+=("NOTION_API_TOKEN")
    fi
    
    # Check Supabase configuration
    if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_API_KEY" ]; then
        missing_vars+=("SUPABASE_URL or SUPABASE_API_KEY")
    fi
    
    # Check AI provider keys
    if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
        missing_vars+=("OPENAI_API_KEY or ANTHROPIC_API_KEY")
    fi
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        error "Missing critical environment variables: ${missing_vars[*]}"
        error "Please ensure all required environment variables are set"
        exit 1
    fi
    
    success "All critical environment variables validated"
}

# Function to test Redis connection
test_redis_connection() {
    log "Testing Redis connection..."
    
    # Install redis-cli if not available (for health checks)
    if ! command -v redis-cli &> /dev/null; then
        log "Installing redis-cli for connection testing..."
        apt-get update && apt-get install -y redis-tools
    fi
    
    # Test Redis connection with proper SSL/TLS if required
    local redis_test_cmd="redis-cli"
    
    # Parse Redis URI to extract components
    if [[ "$REDIS_URI" == *"rediss://"* ]]; then
        redis_test_cmd="$redis_test_cmd --tls"
    fi
    
    # Add password if provided
    if [ -n "$REDIS_PASSWORD" ]; then
        redis_test_cmd="$redis_test_cmd -a $REDIS_PASSWORD"
    fi
    
    # Extract host and port from URI
    local redis_host=$(echo "$REDIS_URI" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    local redis_port=$(echo "$REDIS_URI" | sed -n 's/.*:\([0-9]*\).*/\1/p')
    
    if [ -n "$redis_host" ] && [ -n "$redis_port" ]; then
        redis_test_cmd="$redis_test_cmd -h $redis_host -p $redis_port"
    fi
    
    # Test connection with timeout
    if timeout 10 $redis_test_cmd ping > /dev/null 2>&1; then
        success "Redis connection successful"
    else
        error "Redis connection failed. Please check REDIS_URI and REDIS_PASSWORD"
        error "Redis URI: $REDIS_URI"
        exit 1
    fi
}

# Function to test database connections
test_database_connections() {
    log "Testing database connections..."
    
    # Test MongoDB connection if configured
    if [ -n "$MONGODB_URI" ]; then
        log "Testing MongoDB connection..."
        python3 -c "
import pymongo
import sys
try:
    client = pymongo.MongoClient('$MONGODB_URI', serverSelectionTimeoutMS=5000)
    client.server_info()
    print('MongoDB connection successful')
except Exception as e:
    print(f'MongoDB connection failed: {e}')
    sys.exit(1)
" || exit 1
    fi
    
    # Test Neo4j connection if configured
    if [ -n "$NEO4J_URI" ]; then
        log "Testing Neo4j connection..."
        python3 -c "
from neo4j import GraphDatabase
import sys
try:
    driver = GraphDatabase.driver('$NEO4J_URI', auth=('$NEO4J_USER', '$NEO4J_PASSWORD'))
    with driver.session() as session:
        session.run('RETURN 1')
    driver.close()
    print('Neo4j connection successful')
except Exception as e:
    print(f'Neo4j connection failed: {e}')
    sys.exit(1)
" || exit 1
    fi
    
    success "Database connections validated"
}

# Function to test external API connections
test_api_connections() {
    log "Testing external API connections..."
    
    # Test Notion API
    if [ -n "$NOTION_API_TOKEN" ]; then
        log "Testing Notion API connection..."
        local notion_response=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer $NOTION_API_TOKEN" \
            -H "Notion-Version: 2022-06-28" \
            "https://api.notion.com/v1/users/me")
        
        if [ "$notion_response" = "200" ]; then
            success "Notion API connection successful"
        else
            warning "Notion API connection failed (HTTP $notion_response)"
        fi
    fi
    
    # Test Supabase API
    if [ -n "$SUPABASE_URL" ] && [ -n "$SUPABASE_API_KEY" ]; then
        log "Testing Supabase API connection..."
        local supabase_response=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "apikey: $SUPABASE_API_KEY" \
            -H "Authorization: Bearer $SUPABASE_API_KEY" \
            "$SUPABASE_URL/rest/v1/")
        
        if [ "$supabase_response" = "200" ]; then
            success "Supabase API connection successful"
        else
            warning "Supabase API connection failed (HTTP $supabase_response)"
        fi
    fi
}

# Function to initialize application directories
initialize_directories() {
    log "Initializing application directories..."
    
    # Create necessary directories
    mkdir -p /app/logs /app/cache /app/data /app/tmp
    
    # Set proper permissions
    chmod 755 /app/logs /app/cache /app/data /app/tmp
    
    success "Application directories initialized"
}

# Function to run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Run any necessary database setup scripts
    if [ -f "/app/scripts/migrate.py" ]; then
        python3 /app/scripts/migrate.py
        success "Database migrations completed"
    else
        log "No migration script found, skipping migrations"
    fi
}

# Function to start application with proper error handling
start_application() {
    log "Starting Higher Self Network Server..."
    log "Environment: $ENVIRONMENT"
    log "Command: $*"
    
    # Execute the main command
    exec "$@"
}

# Main execution flow
main() {
    log "Higher Self Network Server - Docker Entrypoint"
    log "================================================"
    
    # Load and validate environment
    load_environment
    
    # Initialize application
    initialize_directories
    
    # Test critical connections
    test_redis_connection
    test_database_connections
    test_api_connections
    
    # Run migrations if needed
    run_migrations
    
    # Start the application
    start_application "$@"
}

# Handle signals for graceful shutdown
trap 'log "Received shutdown signal, stopping application..."; exit 0' SIGTERM SIGINT

# Run main function with all arguments
main "$@"
