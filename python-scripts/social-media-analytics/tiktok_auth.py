"""
TikTok OAuth2 one-time setup.
Run: python tiktok_auth.py
Opens a browser, captures the redirect, saves tiktok_token.json.
After this, tiktok_fetcher.py handles token refresh automatically.
"""
import os
import json
import secrets
import hashlib
import base64
import webbrowser
import urllib.parse
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'tiktok_token.json')
REDIRECT_URI = 'http://localhost:8888/callback'


def _make_code_verifier():
    return secrets.token_urlsafe(64)


def _make_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode()


def _load_token():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _save_token(data):
    tmp = TOKEN_FILE + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f)
    os.replace(tmp, TOKEN_FILE)


def refresh_token(token_data):
    """Exchange refresh_token for a new access_token. Updates tiktok_token.json."""
    client_key    = os.getenv('TIKTOK_CLIENT_KEY', '').strip()
    client_secret = os.getenv('TIKTOK_CLIENT_SECRET', '').strip()
    resp = requests.post(
        'https://open.tiktokapis.com/v2/oauth/token/',
        data={
            'client_key':    client_key,
            'client_secret': client_secret,
            'grant_type':    'refresh_token',
            'refresh_token': token_data['refresh_token'],
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=15
    )
    resp.raise_for_status()
    new_data = resp.json()
    if 'data' in new_data:
        new_data = new_data['data']
    token_data.update(new_data)
    _save_token(token_data)
    return token_data


def get_tiktok_token():
    """Return a valid access_token string. Raises FileNotFoundError if not yet authenticated."""
    data = _load_token()
    if not data:
        raise FileNotFoundError(
            "tiktok_token.json not found.\n"
            "Run: python tiktok_auth.py   (one-time setup)"
        )
    return data.get('access_token', ''), data


def _browser_auth():
    """Run the full OAuth2 PKCE browser flow and save tokens to tiktok_token.json."""
    client_key    = os.getenv('TIKTOK_CLIENT_KEY', '').strip()
    client_secret = os.getenv('TIKTOK_CLIENT_SECRET', '').strip()

    if not client_key or not client_secret:
        print("ERROR: TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET must be set in .env")
        return

    verifier  = _make_code_verifier()
    challenge = _make_code_challenge(verifier)
    state     = secrets.token_urlsafe(16)

    auth_url = (
        'https://www.tiktok.com/v2/auth/authorize/?'
        + urllib.parse.urlencode({
            'client_key':            client_key,
            'response_type':         'code',
            'scope':                 'user.info.basic,video.list',
            'redirect_uri':          REDIRECT_URI,
            'state':                 state,
            'code_challenge':        challenge,
            'code_challenge_method': 'S256',
        })
    )

    captured = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # suppress server logs

        def do_GET(self):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            captured['code']  = params.get('code',  [''])[0]
            captured['state'] = params.get('state', [''])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'<h2>TikTok auth complete. You can close this tab.</h2>')

    print(f"\nOpening TikTok authorization in your browser...")
    print(f"If it doesn't open, go to:\n{auth_url}\n")
    webbrowser.open(auth_url)

    server = HTTPServer(('localhost', 8888), Handler)
    server.handle_request()  # blocks until one request arrives

    if captured.get('state') != state:
        print("ERROR: State mismatch — possible CSRF. Re-run tiktok_auth.py.")
        return

    code = captured.get('code', '')
    if not code:
        print("ERROR: No authorization code received.")
        return

    print("Authorization code received. Exchanging for tokens...")
    resp = requests.post(
        'https://open.tiktokapis.com/v2/oauth/token/',
        data={
            'client_key':    client_key,
            'client_secret': client_secret,
            'code':          code,
            'grant_type':    'authorization_code',
            'redirect_uri':  REDIRECT_URI,
            'code_verifier': verifier,
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=15
    )
    resp.raise_for_status()
    token_data = resp.json()
    if 'data' in token_data:
        token_data = token_data['data']

    _save_token(token_data)
    print(f"\nTikTok tokens saved to tiktok_token.json")
    print(f"Access token expires in: {token_data.get('expires_in', '?')} seconds (~24h)")
    print(f"Refresh token valid for 365 days.")
    print(f"\nYou're all set. Run python main.py to fetch TikTok data.")


if __name__ == '__main__':
    _browser_auth()
