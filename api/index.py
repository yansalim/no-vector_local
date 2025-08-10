import sys
import os
from pathlib import Path

# Add the backend directory to the Python path before importing
current_dir = Path(__file__).parent
backend_path = str(current_dir.parent / "backend")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Set VERCEL environment variable for the backend code
os.environ["VERCEL"] = "1"

# Now import the FastAPI app
app = None
import_error = None

try:
    from main import app

    print("Successfully imported FastAPI app from backend/main.py")
except ImportError as e:
    import_error = str(e)
    print(f"Failed to import main app: {import_error}")
    # Fallback if main.py is not found
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="PDF Chatbot API - Fallback")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def read_root():
        return {"message": "Backend not properly configured", "error": import_error}

    @app.get("/health")
    def health_check():
        return {"status": "fallback", "error": f"Import error: {import_error}"}


# Export the app for Vercel
application = app
