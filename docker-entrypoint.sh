#!/bin/bash
set -e

# Create log directories if they don't exist
mkdir -p logs
mkdir -p /var/log/windsurf

# Check if we need to initialize the database
if [ "${INITIALIZE_DB:-false}" = "true" ]; then
    echo "Initializing database..."
    python -m tools.notion_db_setup
fi

# Check if we're in testing mode
if [ "${TESTING_MODE:-false}" = "true" ]; then
    echo "Running in testing mode..."
    export TEST_MODE=True
    export DISABLE_WEBHOOKS=True
fi

# Execute the command passed to docker run
exec "$@"
