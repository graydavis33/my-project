#!/usr/bin/env python
"""Simple HTTP server to preview trimmed A/B cam videos."""
import http.server
import socketserver
from pathlib import Path

PORT = 3013
TRIM_FOLDER = Path("D:/Sai/05_FOOTAGE_LIBRARY/01_ORGANIZED/Batch_03/Vid_13/Synced/trimmed")

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/video/"):
            # Serve video files
            filename = self.path.split("/")[-1]
            filepath = TRIM_FOLDER / filename
            if filepath.exists():
                self.send_response(200)
                self.send_header("Content-Type", "video/quicktime")
                self.send_header("Content-Length", filepath.stat().st_size)
                self.end_headers()
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
                return
        # Serve other files from current directory
        return super().do_GET()

if __name__ == "__main__":
    handler = MyHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"\n🎬 Preview server running at http://localhost:{PORT}/")
        print(f"Serving trimmed videos from: {TRIM_FOLDER}\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
