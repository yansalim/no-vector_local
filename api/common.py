# Common utilities for Vercel API endpoints
# Copy these functions into each endpoint file to avoid import issues

import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def get_storage_dirs():
    """Get storage directories for serverless environment"""
    upload_dir = Path(tempfile.gettempdir()) / "uploads"
    session_dir = Path(tempfile.gettempdir()) / "sessions"
    upload_dir.mkdir(exist_ok=True)
    session_dir.mkdir(exist_ok=True)
    return upload_dir, session_dir


def load_sessions():
    """Load sessions from disk"""
    sessions = {}
    _, session_dir = get_storage_dirs()

    if session_dir.exists():
        for session_file in session_dir.glob("*.json"):
            try:
                with open(session_file, "r") as f:
                    session_data = json.load(f)
                    session_data["created_at"] = datetime.fromisoformat(
                        session_data["created_at"]
                    )
                    sessions[session_data["session_id"]] = session_data
            except Exception as e:
                print(f"Error loading session {session_file}: {e}")

    return sessions


def save_session(session_id: str, session_data: Dict[str, Any]):
    """Save session to disk"""
    _, session_dir = get_storage_dirs()
    try:
        session_file = session_dir / f"{session_id}.json"
        session_dict = session_data.copy()
        if "created_at" in session_dict and isinstance(
            session_dict["created_at"], datetime
        ):
            session_dict["created_at"] = session_dict["created_at"].isoformat()

        with open(session_file, "w") as f:
            json.dump(session_dict, f)
    except Exception as e:
        print(f"Error saving session {session_id}: {e}")


def send_json_response(handler, data: Dict[str, Any], status_code: int = 200):
    """Send JSON response with proper headers"""
    handler.send_response(status_code)
    handler.send_header("Content-type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header(
        "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
    )
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()

    response_json = json.dumps(data)
    handler.wfile.write(response_json.encode("utf-8"))


def send_error_response(handler, message: str, status_code: int = 500):
    """Send error response"""
    error_data = {"error": message, "status_code": status_code}
    send_json_response(handler, error_data, status_code)


def handle_cors_preflight(handler):
    """Handle CORS preflight requests"""
    handler.send_response(200)
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header(
        "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
    )
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
