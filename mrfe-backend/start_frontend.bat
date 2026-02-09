@echo off
setlocal
set API_PORT=8080
cd /d d:\MRFE2\mrfe-backend\frontend
set VITE_API_BASE_URL=http://127.0.0.1:%API_PORT%
npm install
npm run dev -- --host 0.0.0.0
endlocal
