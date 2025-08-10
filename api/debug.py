from http.server import BaseHTTPRequestHandler
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

    response_json = json.dumps(data, default=str)  # default=str to handle datetime
    handler.wfile.write(response_json.encode("utf-8"))


def handle_cors_preflight(handler):
    """Handle CORS preflight requests"""
    handler.send_response(200)
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header(
        "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
    )
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            upload_dir, session_dir = get_storage_dirs()
            sessions = load_sessions()

            # List all files in session directory
            session_files = []
            if session_dir.exists():
                session_files = [f.name for f in session_dir.glob("*.json")]

            # List all directories in upload directory
            upload_dirs = []
            if upload_dir.exists():
                upload_dirs = [f.name for f in upload_dir.iterdir() if f.is_dir()]

            debug_info = {
                "temp_dir": str(tempfile.gettempdir()),
                "session_dir": str(session_dir),
                "upload_dir": str(upload_dir),
                "session_files": session_files,
                "upload_directories": upload_dirs,
                "loaded_sessions": list(sessions.keys()),
                "session_count": len(sessions),
                "sessions_data": sessions,
            }

            send_json_response(self, debug_info)

        except Exception as e:
            error_data = {"error": str(e), "message": "Debug endpoint failed"}
            send_json_response(self, error_data, 500)

    def do_OPTIONS(self):
        handle_cors_preflight(self)
