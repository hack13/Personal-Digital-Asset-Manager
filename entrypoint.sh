#!/bin/bash

# Wait for database to be ready (if using PostgreSQL)
# until PGPASSWORD=$DATABASE_PASSWORD psql -h "$DATABASE_HOST" -U "$DATABASE_USER" -d "$DATABASE_NAME" -c '\q'; do
#   echo "Waiting for database..."
#   sleep 1
# done

# Apply database migrations
flask db upgrade

# Start gunicorn
exec gunicorn --bind 0.0.0.0:5000 app:app
