@echo off
echo Starting MRFE Backend Server...
set PYTHONPATH=%~dp0;%PYTHONPATH%
python -c "import sys; sys.path.insert(0, '.'); from src.main import app; import uvicorn; print('MRFE Backend Server starting...'); print('Visit http://localhost:8000/docs for API documentation'); uvicorn.run(app, host='0.0.0.0', port=8000)"