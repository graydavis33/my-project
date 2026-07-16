# connect_bank.py
"""One-time, local: open Plaid Link, connect PrimeSouth, capture the read-only
access token, and push it to the PLAID_ACCESS_TOKEN GitHub secret. The token is
never written to a repo file and never printed.

Prereqs: PLAID_CLIENT_ID + PLAID_SECRET in .env, PLAID_ENV=production, and the
`gh` CLI authenticated (`gh auth status`). Run:  python connect_bank.py
"""

import http.server
import json
import os
import subprocess
import webbrowser

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

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
      .then(r => document.body.innerHTML = r.ok
        ? "<h2>Connected. You can close this tab.</h2>"
        : "<h2>Secret upload failed — check the terminal.</h2>");
  },
  onExit: () => {
    fetch("/exit", {method:"POST", body: "{}"});
    document.body.innerHTML = "<h2>Cancelled.</h2>";
  },
});
handler.open();
</script>
Opening Plaid...
</body></html>"""


def main():
    link_token = plaid_client.create_link_token()
    done = {"stop": False}

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            if self.path != "/":
                self.send_response(404); self.end_headers(); return
            self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
            self.wfile.write((PAGE % link_token).encode())
        def do_POST(self):
            if self.path != "/exchange":
                # Link cancelled/abandoned — stop the server instead of hanging forever
                self.send_response(200); self.end_headers()
                done["stop"] = True
                print("Cancelled — no secret was set. Re-run to try again.")
                return
            body = self.rfile.read(int(self.headers["Content-Length"]))
            public_token = json.loads(body)["public_token"]
            access_token = plaid_client.exchange_public_token(public_token)
            # Secure the token in the local gitignored .env FIRST — the exchange
            # is one-shot, so if the GitHub push fails the bank login isn't wasted
            # (and GitHub secrets are write-only, we can't read it back later).
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
            with open(env_path, "a") as f:
                f.write(f"\nPLAID_ACCESS_TOKEN={access_token}\n")
            try:
                subprocess.run(["gh", "secret", "set", "PLAID_ACCESS_TOKEN", "--repo", REPO],
                               input=access_token, text=True, check=True)
                gh_msg = "GitHub secret set"
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                # gh never echoes stdin, so nothing leaked; token is safe in .env
                gh_msg = (f"GitHub secret NOT set ({type(e).__name__}) — token saved to local "
                          ".env; push it to GitHub later (no bank re-login needed)")
            self.send_response(200); self.end_headers()
            done["stop"] = True
            print(f"PrimeSouth connected. Token: local .env OK; {gh_msg}.")

    srv = http.server.HTTPServer(("127.0.0.1", PORT), H)
    webbrowser.open(f"http://127.0.0.1:{PORT}/")
    print(f"Complete the bank login in your browser ({srv.server_address[0]}:{PORT})...")
    while not done["stop"]:
        srv.handle_request()
    srv.server_close()


if __name__ == "__main__":
    main()
