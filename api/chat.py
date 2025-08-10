from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
from _utils import (
    sessions,
    send_json_response,
    send_error_response,
    handle_cors_preflight,
)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Parse request body
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode("utf-8"))

            session_id = request_data.get("session_id")
            question = request_data.get("question")
            model = request_data.get("model", "gpt-5-mini")
            chat_history = request_data.get("chat_history", [])

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
