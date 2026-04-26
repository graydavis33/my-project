import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file',
]

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(HERE, 'token.json')
SECRET_PATH = os.path.join(HERE, 'client_secret.json')


def get_credentials():
    """Get or refresh Google OAuth credentials. Opens browser on first run."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(SECRET_PATH):
                raise FileNotFoundError(
                    f"\n\nERROR: client_secret.json not found at {SECRET_PATH}\n"
                    "Copy it from python-scripts/social-media-analytics/client_secret.json\n"
                )
            flow = InstalledAppFlow.from_client_secrets_file(SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

    return creds


if __name__ == "__main__":
    creds = get_credentials()
    print(f"Google auth successful. token.json saved at: {TOKEN_PATH}")
