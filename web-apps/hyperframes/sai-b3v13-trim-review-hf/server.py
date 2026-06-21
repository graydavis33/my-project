#!/usr/bin/env python
import sys
sys.stdout.reconfigure(encoding="utf-8")
import http.server
import socketserver
from pathlib import Path

PORT = 3014
FOLDER = Path(__file__).parent
VIDEO_DIR = Path("D:/Sai/08_AI_EDITS/shorts/Batch_03/B3_V13 - The Real Lover Is You")

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve video files with range support
        if self.path.startswith("/B3_V13_"):
            filename = self.path.lstrip("/")
            filepath = VIDEO_DIR / filename

            if not filepath.exists():
                self.send_response(404)
                self.end_headers()
                return

            file_size = filepath.stat().st_size
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
    import os
    os.chdir(FOLDER)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n🎬 Preview at http://localhost:{PORT}/")
        print(f"Serving from: {FOLDER}\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
