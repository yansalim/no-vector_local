from http.server import BaseHTTPRequestHandler
import json
import uuid
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


def save_session(session_id: str, session_data: Dict[str, Any]):
    """Save session to disk"""
    _, session_dir = get_storage_dirs()
    session_file = session_dir / f"{session_id}.json"
    session_dict = session_data.copy()
    if "created_at" in session_dict and isinstance(
        session_dict["created_at"], datetime
    ):
        session_dict["created_at"] = session_dict["created_at"].isoformat()
    print(session_file)
    with open(session_file, "w") as f:
        json.dump(session_dict, f)

    # Load the saved file back and print it to check validity
    with open(session_file, "r") as f:
        loaded_data = json.load(f)
        print(f"Loaded session data for validation: {loaded_data}")
    print(f"Session saved: {session_id}")


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
    def do_POST(self):
        try:
            # Create new session
            session_id = str(uuid.uuid4())

            # Create session data (placeholder for now)
            session_data = {
                "session_id": session_id,
                "description": "Uploaded documents",
                "documents": [],  # TODO: Process actual uploaded files
                "created_at": datetime.now(),
                "total_session_cost": 0.0,
            }

            # Save session to disk
            save_session(session_id, session_data)

            # Create session directory for files
            upload_dir, _ = get_storage_dirs()
            session_upload_dir = upload_dir / session_id
            session_upload_dir.mkdir(exist_ok=True)

            response = {
                "message": "Session created successfully",
                "session_id": session_id,
                "note": "File processing not yet fully implemented",
            }

            send_json_response(self, response)

        except Exception as e:
            print(f"Error in upload endpoint: {e}")
            send_error_response(self, f"Upload failed: {str(e)}")

    def do_OPTIONS(self):
        handle_cors_preflight(self)
