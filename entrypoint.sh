#!/bin/bash

# Function to check required environment variables
check_required_vars() {
    local missing_vars=0
    for var in "$@"; do
        if [ -z "${!var}" ]; then
            echo "Error: Required environment variable $var is not set"
            missing_vars=1
        fi
    done
    if [ $missing_vars -eq 1 ]; then
        exit 1
    fi
}

# Check required environment variables (add your required variables here)
check_required_vars "FLASK_APP" "FLASK_ENV" "STORAGE_URL"

# Wait for database to be ready (if using PostgreSQL)
# until PGPASSWORD=$DATABASE_PASSWORD psql -h "$DATABASE_HOST" -U "$DATABASE_USER" -d "$DATABASE_NAME" -c '\q'; do
#   echo "Waiting for database..."
#   sleep 1
# done

# Apply database migrations
flask db upgrade

# Start gunicorn with proper environment handling
exec gunicorn --bind 0.0.0.0:5000 \
    --env FLASK_APP=${FLASK_APP} \
    --env FLASK_ENV=${FLASK_ENV} \
    --env STORAGE_URL=${STORAGE_URL} \
    app:app
