from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
from _utils import (
    sessions,
    send_json_response,
    send_error_response,
    handle_cors_preflight,
    save_session_to_disk,
)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Parse URL to get session_id
            parsed_url = urllib.parse.urlparse(self.path)
            path_parts = parsed_url.path.strip("/").split("/")

            # Expect path like /api/session/{session_id}/documents
            if len(path_parts) < 4:
                send_error_response(self, "Session ID required", 400)
                return

            session_id = path_parts[2]  # /api/session/{session_id}/documents

            if session_id not in sessions:
                send_error_response(self, "Session not found", 404)
                return

            # For now, return a placeholder response
            # TODO: Implement actual file upload and processing
            response_data = {
                "session_id": session_id,
                "message": "Documents endpoint reached - file processing not yet implemented",
                "new_documents_count": 0,
            }

            send_json_response(self, response_data)

        except Exception as e:
            print(f"Error in documents endpoint: {e}")
            send_error_response(self, f"Internal server error: {str(e)}")

    def do_OPTIONS(self):
        handle_cors_preflight(self)
