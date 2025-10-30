#!/bin/bash
# Railway startup script with automatic migrations

set -e  # Exit on error

echo "🚂 RAILWAY DEPLOYMENT - Starting..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    exit 1
fi

echo "✅ Database URL configured"

# Run Alembic migrations
echo "🔄 Running Alembic migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "⚠️ Migration failed, but continuing (tables may already exist)"
fi

# Start Gunicorn server
echo "🚀 Starting Gunicorn server..."
exec gunicorn --bind=0.0.0.0:$PORT \
              --workers=4 \
              --timeout=120 \
              --preload \
              --access-logfile=- \
              --error-logfile=- \
              --log-level=info \
              main:app
