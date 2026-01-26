@echo off
REM Start Celery workers and beat scheduler (Windows)

echo Starting Celery workers...

REM Default queue worker
start "Celery Worker Default" cmd /k "celery -A app.tasks.celery_app worker -l info -Q default -c 4 --hostname=worker-default@%%h"

REM Risk queue worker
start "Celery Worker Risk" cmd /k "celery -A app.tasks.celery_app worker -l info -Q risk -c 2 --hostname=worker-risk@%%h"

REM Notifications queue worker
start "Celery Worker Notifications" cmd /k "celery -A app.tasks.celery_app worker -l info -Q notifications -c 2 --hostname=worker-notifications@%%h"

REM Reports queue worker
start "Celery Worker Reports" cmd /k "celery -A app.tasks.celery_app worker -l info -Q reports -c 2 --hostname=worker-reports@%%h"

REM Data queue worker
start "Celery Worker Data" cmd /k "celery -A app.tasks.celery_app worker -l info -Q data -c 2 --hostname=worker-data@%%h"

REM Beat scheduler
echo Starting Celery beat...
start "Celery Beat" cmd /k "celery -A app.tasks.celery_app beat -l info"

REM Flower monitoring (optional)
if "%ENABLE_FLOWER%"=="true" (
    echo Starting Flower...
    start "Flower" cmd /k "celery -A app.tasks.celery_app flower --port=5555"
)

echo All Celery services started
pause
