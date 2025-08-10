from http.server import BaseHTTPRequestHandler
import urllib.parse
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json


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
            upload_dir, _ = get_storage_dirs()

            # Parse URL to get session_id and filename
            parsed_url = urllib.parse.urlparse(self.path)
            path_parts = parsed_url.path.strip("/").split("/")

            # Expect path like /api/pdf/{session_id}/{filename}
            if len(path_parts) < 4:
                send_error_response(self, "Session ID and filename required", 400)
                return

            session_id = path_parts[2]  # /api/pdf/{session_id}/{filename}
            filename = urllib.parse.unquote(
                path_parts[3]
            )  # Decode URL-encoded filename

            if session_id not in sessions:
                send_error_response(self, "Session not found", 404)
                return

            # Construct file path
            file_path = upload_dir / session_id / filename

            if not file_path.exists():
                send_error_response(self, "File not found", 404)
                return

            # Serve the PDF file
            self.send_response(200)
            self.send_header("Content-type", "application/pdf")
            self.send_header("Content-Disposition", f"inline; filename={filename}")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            # Read and send file content
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())

        except Exception as e:
            print(f"Error in PDF endpoint: {e}")
            send_error_response(self, f"Internal server error: {str(e)}")

    def do_OPTIONS(self):
        handle_cors_preflight(self)
