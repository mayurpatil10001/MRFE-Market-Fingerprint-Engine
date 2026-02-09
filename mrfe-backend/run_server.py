import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("."))

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.abspath("."), "src"))

if __name__ == "__main__":
    # Import and run the application
    import uvicorn

    from src.main import app

    host = "127.0.0.1"
    port = 8001
    print("Starting MRFE Backend Server...")
    print(f"Frontend dashboard: http://{host}:{port}/")
    print(f"API documentation: http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port)
