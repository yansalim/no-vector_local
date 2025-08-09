import sys
import os

# Add the backend directory to the Python path before importing
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Now import the FastAPI app
try:
    from main import app
except ImportError:
    # Fallback if main.py is not found
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/")
    def read_root():
        return {"message": "Backend not properly configured"}
