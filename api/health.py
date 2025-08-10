from http.server import BaseHTTPRequestHandler
from _utils import send_json_response, handle_cors_preflight


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        response_data = {"status": "healthy"}
        send_json_response(self, response_data)

    def do_OPTIONS(self):
        handle_cors_preflight(self)
