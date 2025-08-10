from http.server import BaseHTTPRequestHandler
import urllib.parse
import os
from _utils import sessions, send_error_response, handle_cors_preflight, UPLOAD_DIR


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
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
            file_path = UPLOAD_DIR / session_id / filename

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
