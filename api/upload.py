import sys
import os
import json
import tempfile
from http.server import BaseHTTPRequestHandler

# from urllib.parse import parse_qs  # Not used
import cgi

# Add the backend directory to the Python path before importing
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from models import UploadResponse, DocumentData, DocumentPage
from pdf_processor import PDFProcessor


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Initialize PDF processor
            pdf_processor = PDFProcessor()

            # Set CORS headers
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            # Parse multipart form data
            content_type = self.headers["content-type"]
            if not content_type.startswith("multipart/form-data"):
                self.wfile.write(
                    json.dumps(
                        {"error": "Content-Type must be multipart/form-data"}
                    ).encode()
                )
                return

            # Parse the form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers["content-type"],
                },
            )

            # Get description from form
            description = form.getvalue("description", "")

            # Get uploaded files
            files = []
            if "files" in form:
                if isinstance(form["files"], list):
                    files = form["files"]
                else:
                    files = [form["files"]]

            if len(files) > 100:
                self.wfile.write(
                    json.dumps({"error": "Maximum 100 documents allowed"}).encode()
                )
                return

            # Process files and extract text
            documents = []
            for i, file_item in enumerate(files):
                if not hasattr(file_item, "filename") or not file_item.filename:
                    continue

                if not file_item.filename.endswith(".pdf"):
                    self.wfile.write(
                        json.dumps({"error": "Only PDF files are allowed"}).encode()
                    )
                    return

                # Create temporary file for processing
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as temp_file:
                    temp_file.write(file_item.file.read())
                    temp_file_path = temp_file.name

                try:
                    # Extract text from PDF
                    pages_data = pdf_processor.extract_pages(temp_file_path)

                    # Convert to DocumentPage objects
                    pages = [
                        DocumentPage(page_number=page["page_number"], text=page["text"])
                        for page in pages_data
                    ]

                    documents.append(
                        DocumentData(
                            id=i + 1,
                            filename=file_item.filename,
                            pages=pages,
                            total_pages=len(pages),
                        )
                    )
                except Exception as e:
                    print(f"PDF processing error for {file_item.filename}: {str(e)}")
                    self.wfile.write(
                        json.dumps(
                            {
                                "error": f"Error processing {file_item.filename}: {str(e)}"
                            }
                        ).encode()
                    )
                    return
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_file_path)
                    except OSError:
                        pass

            # Create response
            response = UploadResponse(
                documents=documents,
                message=f"Successfully processed {len(files)} documents",
            )

            # Send response
            self.wfile.write(response.model_dump_json().encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"error": f"Internal server error: {str(e)}"}).encode()
            )

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
