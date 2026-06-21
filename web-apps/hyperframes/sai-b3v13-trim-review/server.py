#!/usr/bin/env python
"""Simple HTTP server to preview trimmed A/B cam videos with Range request support."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import http.server
import socketserver
from pathlib import Path
from urllib.parse import unquote

PORT = 3013
TRIM_FOLDER = Path("D:/Sai/08_AI_EDITS/shorts/Batch_03/B3_V13 - The Real Lover Is You")

class VideoStreamHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/video/"):
            filename = unquote(self.path.split("/")[-1])
            filepath = TRIM_FOLDER / filename

            if not filepath.exists():
                self.send_response(404)
                self.end_headers()
                return

            file_size = filepath.stat().st_size

            # Handle Range requests for streaming
            range_header = self.headers.get("Range")
            if range_header:
                range_match = range_header.replace("bytes=", "").split("-")
                start = int(range_match[0]) if range_match[0] else 0
                end = int(range_match[1]) if range_match[1] else file_size - 1

                if start < 0 or end >= file_size or start > end:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{file_size}")
                    self.end_headers()
                    return

                self.send_response(206)
                self.send_header("Content-Type", "video/quicktime")
                self.send_header("Content-Length", end - start + 1)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                with open(filepath, "rb") as f:
                    f.seek(start)
                    self.wfile.write(f.read(end - start + 1))
            else:
                self.send_response(200)
                self.send_header("Content-Type", "video/quicktime")
                self.send_header("Content-Length", file_size)
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
            return

        return super().do_GET()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), VideoStreamHandler) as httpd:
        print(f"\n🎬 Preview server running at http://localhost:{PORT}/")
        print(f"Serving videos from: {TRIM_FOLDER}\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
