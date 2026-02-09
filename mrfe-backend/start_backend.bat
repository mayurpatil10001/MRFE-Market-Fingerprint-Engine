@echo off
setlocal
set API_PORT=8080
cd /d d:\MRFE2\mrfe-backend
python -m uvicorn src.main:app --reload --port %API_PORT%
endlocal
