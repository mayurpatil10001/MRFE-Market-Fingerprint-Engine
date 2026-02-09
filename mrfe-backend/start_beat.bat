@echo off
setlocal
cd /d d:\MRFE2\mrfe-backend
celery -A src.workers.celery_app.celery_app beat -l info
endlocal
