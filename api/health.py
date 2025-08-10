from http.server import BaseHTTPRequestHandler
import json


def send_json_response(handler, data, status_code=200):
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
        response_data = {"status": "healthy"}
        send_json_response(self, response_data)

    def do_OPTIONS(self):
        handle_cors_preflight(self)
