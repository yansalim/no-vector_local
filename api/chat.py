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
            # Load sessions fresh each time (serverless)
            sessions = load_sessions()

            # Parse request body
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode("utf-8"))

            session_id = request_data.get("session_id")
            question = request_data.get("question")

            if not session_id:
                send_error_response(self, "Session ID required", 400)
                return

            if not question:
                send_error_response(self, "Question required", 400)
                return

            if session_id not in sessions:
                send_error_response(self, "Session not found", 404)
                return

            # For now, return a placeholder response
            # TODO: Implement actual LLM integration
            response_data = {
                "type": "complete",
                "answer": f"This is a placeholder response for: {question}",
                "session_cost": 0.001,
                "timing_breakdown": {
                    "document_selection": 0.1,
                    "page_detection": 0.2,
                    "answer_generation": 0.5,
                    "total_time": 0.8,
                },
                "cost_breakdown": {
                    "document_selection": 0.0001,
                    "page_detection": 0.0002,
                    "answer_generation": 0.0007,
                    "total_cost": 0.001,
                },
                "message": "Chat endpoint working but LLM integration needed",
            }

            send_json_response(self, response_data)

        except json.JSONDecodeError:
            send_error_response(self, "Invalid JSON", 400)
        except Exception as e:
            print(f"Error in chat endpoint: {e}")
            send_error_response(self, f"Internal server error: {str(e)}")

    def do_OPTIONS(self):
        handle_cors_preflight(self)
