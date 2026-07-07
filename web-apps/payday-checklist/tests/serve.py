"""serve.py — shared static server for payday e2e tests, plus /fake/* in-memory sync backend."""
import http.server, json, os, socketserver, threading

WEBAPPS_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

FAKE = {"docs": {}, "rev": 0}   # {"docs": {"transactions/abc": {...}}, "rev": n}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=WEBAPPS_DIR, **kw)
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.startswith("/fake/state"):
            body = json.dumps(FAKE).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()
    def do_POST(self):
        if self.path == "/fake/set":
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n))
            FAKE["docs"][payload["path"]] = payload["data"]
            FAKE["rev"] += 1
            self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers()
            self.wfile.write(b"{}")
            return
        if self.path == "/fake/reset":
            FAKE["docs"] = {}; FAKE["rev"] = 0
            self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers()
            self.wfile.write(b"{}")
            return
        self.send_response(404); self.end_headers()

def start_server(port):
    socketserver.TCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd
