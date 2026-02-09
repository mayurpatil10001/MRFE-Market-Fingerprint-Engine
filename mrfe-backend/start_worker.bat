@echo off
setlocal
cd /d d:\MRFE2\mrfe-backend
celery -A src.workers.celery_app.celery_app worker -l info -Q default,events,fingerprints,forecasts,maintenance
endlocal
