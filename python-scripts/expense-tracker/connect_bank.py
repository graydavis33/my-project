# connect_bank.py
"""One-time, local: open Plaid Link, connect PrimeSouth, capture the read-only
access token, and push it to the PLAID_ACCESS_TOKEN GitHub secret. The token is
never written to a repo file and never printed.

Prereqs: PLAID_CLIENT_ID + PLAID_SECRET in .env, PLAID_ENV=production, and the
`gh` CLI authenticated (`gh auth status`). Run:  python connect_bank.py
"""

import http.server
import json
import subprocess
import urllib.parse
import webbrowser

import plaid_client

REPO = "graydavis33/my-project"
PORT = 8712

PAGE = """<!doctype html><html><body>
<script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
<script>
const handler = Plaid.create({
  token: "%s",
  onSuccess: (public_token) => {
    fetch("/exchange", {method:"POST", body: JSON.stringify({public_token})})
      .then(() => document.body.innerHTML = "<h2>Connected. You can close this tab.</h2>");
  },
  onExit: () => document.body.innerHTML = "<h2>Cancelled.</h2>",
});
handler.open();
</script>
Opening Plaid...
</body></html>"""


def main():
    link_token = plaid_client.create_link_token()
    done = {"ok": False}

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
            self.wfile.write((PAGE % link_token).encode())
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            public_token = json.loads(body)["public_token"]
            access_token = plaid_client.exchange_public_token(public_token)
            subprocess.run(["gh", "secret", "set", "PLAID_ACCESS_TOKEN", "--repo", REPO],
                           input=access_token, text=True, check=True)
            self.send_response(200); self.end_headers()
            done["ok"] = True
            print("PLAID_ACCESS_TOKEN secret set. PrimeSouth connected.")

    srv = http.server.HTTPServer(("127.0.0.1", PORT), H)
    webbrowser.open(f"http://127.0.0.1:{PORT}/")
    print(f"Complete the bank login in your browser ({srv.server_address[0]}:{PORT})...")
    while not done["ok"]:
        srv.handle_request()


if __name__ == "__main__":
    main()
