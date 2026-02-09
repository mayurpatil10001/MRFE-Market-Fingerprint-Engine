@echo off
setlocal
set API_PORT=8080
start "MRFE API" cmd /k "cd /d d:\\MRFE2\\mrfe-backend && python -m uvicorn src.main:app --reload --port %API_PORT%"
start "MRFE UI" cmd /k "cd /d d:\\MRFE2\\mrfe-backend\\frontend && set VITE_API_BASE_URL=http://127.0.0.1:%API_PORT% && npm install && npm run dev -- --host 0.0.0.0"
endlocal
