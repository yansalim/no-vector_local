from http.server import BaseHTTPRequestHandler
import urllib.parse
from _utils import (
    sessions,
    send_json_response,
    send_error_response,
    handle_cors_preflight,
)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse URL to get session_id
            parsed_url = urllib.parse.urlparse(self.path)
            path_parts = parsed_url.path.strip("/").split("/")

            # Expect path like /api/session/{session_id}
            if len(path_parts) < 3:
                send_error_response(self, "Session ID required", 400)
                return

            session_id = path_parts[2]  # /api/session/{session_id}

            if session_id not in sessions:
                send_error_response(self, "Session not found", 404)
                return

            session_data = sessions[session_id]

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
