"""
Shared utilities for Vercel API endpoints
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Storage directories - use /tmp for serverless environments
UPLOAD_DIR = Path(tempfile.gettempdir()) / "uploads"
SESSION_DIR = Path(tempfile.gettempdir()) / "sessions"

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
SESSION_DIR.mkdir(exist_ok=True)

# In-memory storage for sessions
sessions: Dict[str, Any] = {}


def load_sessions_from_disk():
    """Load sessions from JSON files on disk"""
    global sessions
    if SESSION_DIR.exists():
        for session_file in SESSION_DIR.glob("*.json"):
            try:
                with open(session_file, "r") as f:
                    session_data = json.load(f)
                    # Convert timestamp back to datetime
                    session_data["created_at"] = datetime.fromisoformat(
                        session_data["created_at"]
                    )
                    sessions[session_data["session_id"]] = session_data
                    print(f"Loaded session: {session_data['session_id']}")
            except Exception as e:
                print(f"Error loading session {session_file}: {e}")


def save_session_to_disk(session_id: str, session_data: Dict[str, Any]):
    """Save session to disk"""
    try:
        session_file = SESSION_DIR / f"{session_id}.json"
        # Convert datetime to string for JSON serialization
        session_dict = session_data.copy()
        if "created_at" in session_dict and isinstance(
            session_dict["created_at"], datetime
        ):
            session_dict["created_at"] = session_dict["created_at"].isoformat()

        with open(session_file, "w") as f:
            json.dump(session_dict, f)
        print(f"Saved session: {session_id}")
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


def get_path_params(path: str, pattern: str) -> Dict[str, str]:
    """Extract path parameters from URL"""
    # Simple parameter extraction for patterns like /api/session/{session_id}
    path_parts = path.strip("/").split("/")
    pattern_parts = pattern.strip("/").split("/")

    params = {}
    for i, pattern_part in enumerate(pattern_parts):
        if pattern_part.startswith("{") and pattern_part.endswith("}"):
            param_name = pattern_part[1:-1]  # Remove { }
            if i < len(path_parts):
                params[param_name] = path_parts[i]

    return params


# Load sessions on import
load_sessions_from_disk()
