#!/bin/bash

# Start Celery workers and beat scheduler

echo "Starting Celery workers..."

# Default queue worker
celery -A app.tasks.celery_app worker \
    -l info \
    -Q default \
    -c 4 \
    --hostname=worker-default@%h &

# Risk queue worker
celery -A app.tasks.celery_app worker \
    -l info \
    -Q risk \
    -c 2 \
    --hostname=worker-risk@%h &

# Notifications queue worker
celery -A app.tasks.celery_app worker \
    -l info \
    -Q notifications \
    -c 2 \
    --hostname=worker-notifications@%h &

# Reports queue worker
celery -A app.tasks.celery_app worker \
    -l info \
    -Q reports \
    -c 2 \
    --hostname=worker-reports@%h &

# Data queue worker
celery -A app.tasks.celery_app worker \
    -l info \
    -Q data \
    -c 2 \
    --hostname=worker-data@%h &

# Beat scheduler
echo "Starting Celery beat..."
celery -A app.tasks.celery_app beat -l info &

# Flower monitoring (optional)
if [ "$ENABLE_FLOWER" = "true" ]; then
    echo "Starting Flower..."
    celery -A app.tasks.celery_app flower --port=5555 &
fi

echo "All Celery services started"

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
