"""
One-time helper: copies Slack tokens from email-agent/.env into this project's .env.
Run this before setup.py to pre-fill the Slack section automatically.

Usage: python copy_slack_env.py
"""

import os
import re
from pathlib import Path

EMAIL_AGENT_ENV = Path(__file__).parent.parent / 'email-agent' / '.env'
THIS_ENV        = Path(__file__).parent / '.env'

KEYS_TO_COPY = ['SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN', 'SLACK_USER_ID', 'ANTHROPIC_API_KEY']


def main():
    if not EMAIL_AGENT_ENV.exists():
        print(f"email-agent .env not found at: {EMAIL_AGENT_ENV}")
        return

    # Read source
    source_vals = {}
    for line in EMAIL_AGENT_ENV.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.startswith('#'):
            k, _, v = line.partition('=')
            k = k.strip()
            if k in KEYS_TO_COPY:
                source_vals[k] = v.strip()

    # Create .env from example if it doesn't exist
    example = THIS_ENV.parent / '.env.example'
    if not THIS_ENV.exists() and example.exists():
        import shutil
        shutil.copy(example, THIS_ENV)
        print("Created .env from .env.example")

    if not THIS_ENV.exists():
        THIS_ENV.write_text('')

    # Read current .env
    content = THIS_ENV.read_text(encoding='utf-8')

    # Replace or append each key
    for key, val in source_vals.items():
        pattern = rf'^{key}=.*$'
        replacement = f'{key}={val}'
        if re.search(pattern, content, re.MULTILINE):
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        else:
            content += f'\n{key}={val}'

    THIS_ENV.write_text(content, encoding='utf-8')
    print(f"Copied {len(source_vals)} keys: {', '.join(source_vals.keys())}")
    print("Now fill in the remaining keys in .env, then run: python setup.py")


if __name__ == '__main__':
    main()
