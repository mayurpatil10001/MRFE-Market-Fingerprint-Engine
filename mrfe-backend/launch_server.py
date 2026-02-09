import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now import and run the application
from main import app
import uvicorn

print("Starting MRFE Backend Server...")
print("API Documentation available at: http://localhost:8000/docs")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)