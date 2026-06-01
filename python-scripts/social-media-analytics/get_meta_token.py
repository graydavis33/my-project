"""
get_meta_token.py — One-time Meta token setup script.

Usage:
  1. Add META_APP_ID and META_APP_SECRET to your .env (from Meta Developer dashboard)
  2. Get a short-lived User Access Token from Graph API Explorer (see instructions below)
  3. Run: python get_meta_token.py <your_short_lived_token>

The script will:
  - Exchange for a long-lived token (60 days)
  - Find your Facebook Page and get a permanent Page Access Token
  - Find your Instagram Business Account ID
  - Write META_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID, FACEBOOK_PAGE_ID to .env
"""

import os
import sys
import re
import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH = 'https://graph.facebook.com/v19.0'


def exchange_for_long_lived(short_token):
    """Exchange a short-lived user token for a 60-day long-lived token."""
    app_id     = os.getenv('META_APP_ID', '').strip()
    app_secret = os.getenv('META_APP_SECRET', '').strip()
    if not app_id or not app_secret:
        print("ERROR: META_APP_ID and META_APP_SECRET must be in your .env file.")
        print("  Get them from: developers.facebook.com → Your App → App Settings → Basic")
        sys.exit(1)

    resp = requests.get(f'{GRAPH}/oauth/access_token', params={
        'grant_type':        'fb_exchange_token',
        'client_id':         app_id,
        'client_secret':     app_secret,
        'fb_exchange_token': short_token,
    })
    resp.raise_for_status()
    data = resp.json()
    if 'access_token' not in data:
        print(f"ERROR: Token exchange failed — {data}")
        sys.exit(1)
    return data['access_token']


def get_page_token(long_lived_token):
    """Get a permanent Page Access Token for your Facebook Page."""
    resp = requests.get(f'{GRAPH}/me/accounts', params={'access_token': long_lived_token})
    resp.raise_for_status()
    pages = resp.json().get('data', [])
    if not pages:
        print("ERROR: No Facebook Pages found on this account.")
        print("  Make sure your Facebook Page is linked to this account.")
        sys.exit(1)

    if len(pages) == 1:
        page = pages[0]
    else:
        print("\nMultiple Facebook Pages found. Pick one:")
        for i, p in enumerate(pages):
            print(f"  [{i}] {p['name']} (ID: {p['id']})")
        choice = int(input("Enter number: ").strip())
        page = pages[choice]

    print(f"  → Page: {page['name']} (ID: {page['id']})")
    return page['id'], page['access_token']


def get_instagram_account_id(page_id, page_token):
    """Get the Instagram Business Account ID connected to the Facebook Page."""
    resp = requests.get(f'{GRAPH}/{page_id}', params={
        'fields':       'instagram_business_account',
        'access_token': page_token,
    })
    resp.raise_for_status()
    data = resp.json()
    ig = data.get('instagram_business_account', {})
    ig_id = ig.get('id', '')
    if not ig_id:
        print("ERROR: No Instagram Business Account linked to this Page.")
        print("  Make sure your Instagram is a Business/Creator account linked to your Facebook Page.")
        sys.exit(1)
    print(f"  → Instagram Business Account ID: {ig_id}")
    return ig_id


def write_to_env(page_token, ig_id, page_id):
    """Write the three new vars into .env, replacing existing values if present."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')

    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()

    def set_var(text, key, value):
        pattern = rf'^{key}=.*$'
        replacement = f'{key}={value}'
        if re.search(pattern, text, flags=re.MULTILINE):
            return re.sub(pattern, replacement, text, flags=re.MULTILINE)
        else:
            return text.rstrip('\n') + f'\n{key}={value}\n'

    content = set_var(content, 'META_ACCESS_TOKEN', page_token)
    content = set_var(content, 'INSTAGRAM_BUSINESS_ACCOUNT_ID', ig_id)
    content = set_var(content, 'FACEBOOK_PAGE_ID', page_id)

    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n  → Written to .env:")
    print(f"      META_ACCESS_TOKEN              = {page_token[:20]}...")
    print(f"      INSTAGRAM_BUSINESS_ACCOUNT_ID  = {ig_id}")
    print(f"      FACEBOOK_PAGE_ID               = {page_id}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    short_token = sys.argv[1].strip()

    print("\n[1/4] Exchanging short-lived token for long-lived token (60 days)...")
    long_token = exchange_for_long_lived(short_token)
    print("  → Got long-lived user token.")

    print("\n[2/4] Finding your Facebook Page...")
    page_id, page_token = get_page_token(long_token)

    print("\n[3/4] Finding your Instagram Business Account ID...")
    ig_id = get_instagram_account_id(page_id, page_token)

    print("\n[4/4] Writing to .env...")
    write_to_env(page_token, ig_id, page_id)

    print("\nDone. Now run: python main.py")
    print("Instagram and Facebook data will come from the Graph API instead of the broken scraper.")


if __name__ == '__main__':
    main()
