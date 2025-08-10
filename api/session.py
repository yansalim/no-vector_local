from http.server import BaseHTTPRequestHandler
import urllib.parse
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
        print(f"Loading sessions from {session_dir}")
        for session_file in session_dir.glob("*.json"):
            print("Loading something")
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


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Load sessions fresh each time (serverless)
            sessions = load_sessions()
            print(f"Loaded {len(sessions)} sessions: {list(sessions.keys())}")

            # Parse URL to get session_id
            parsed_url = urllib.parse.urlparse(self.path)
            path_parts = parsed_url.path.strip("/").split("/")
            print(f"Request path: {self.path}, parsed parts: {path_parts}")

            # Expect path like /api/session/{session_id}
            if len(path_parts) < 3:
                send_error_response(self, "Session ID required", 400)
                return

            session_id = path_parts[2]  # /api/session/{session_id}
            print(f"Looking for session_id: {session_id}")

            if session_id not in sessions:
                print(
                    f"Session {session_id} not found in available sessions: {list(sessions.keys())}"
                )
                send_error_response(self, "Session not found", 404)
                return

            session_data = sessions[session_id]
            print(f"Found session data for {session_id}")

            # Prepare response data
            response_data = {
                "session_id": session_id,
                "description": session_data.get("description", ""),
                "documents": session_data.get("documents", []),
                "created_at": session_data.get("created_at"),
                "total_session_cost": session_data.get("total_session_cost", 0.0),
            }

            # Convert datetime to string if needed
            if hasattr(response_data["created_at"], "isoformat"):
                response_data["created_at"] = response_data["created_at"].isoformat()

            send_json_response(self, response_data)

        except Exception as e:
            print(f"Error in session endpoint: {e}")
            send_error_response(self, f"Internal server error: {str(e)}")

    def do_OPTIONS(self):
        handle_cors_preflight(self)
