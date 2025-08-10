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
    def do_PUT(self):
        try:
            # Parse URL to get session_id
            parsed_url = urllib.parse.urlparse(self.path)
            path_parts = parsed_url.path.strip("/").split("/")

            # Expect path like /api/session/{session_id}/description
            if len(path_parts) < 4:
                send_error_response(self, "Session ID required", 400)
                return

            session_id = path_parts[2]  # /api/session/{session_id}/description

            if session_id not in sessions:
                send_error_response(self, "Session not found", 404)
                return

            # Parse request body
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode("utf-8"))

            new_description = request_data.get("description")
            if not new_description:
                send_error_response(self, "Description required", 400)
                return

            # Update session description
            sessions[session_id]["description"] = new_description

            # Save to disk
            save_session_to_disk(session_id, sessions[session_id])

            response_data = {
                "message": "Description updated successfully",
                "description": new_description,
            }

            send_json_response(self, response_data)

        except json.JSONDecodeError:
            send_error_response(self, "Invalid JSON", 400)
        except Exception as e:
            print(f"Error in description endpoint: {e}")
            send_error_response(self, f"Internal server error: {str(e)}")

    def do_OPTIONS(self):
        handle_cors_preflight(self)
