import sys
import os
import re
import argparse

sys.stdout.reconfigure(encoding="utf-8")

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from auth import get_credentials


def extract_doc_id(doc_id_or_url):
    """Accept either a raw doc ID or a full Google Docs URL."""
    if 'docs.google.com' in doc_id_or_url:
        m = re.search(r'/document/d/([a-zA-Z0-9_-]+)', doc_id_or_url)
        if m:
            return m.group(1)
        raise ValueError(f"Could not extract doc ID from URL: {doc_id_or_url}")
    return doc_id_or_url


def get_services():
    creds = get_credentials()
    docs = build('docs', 'v1', credentials=creds)
    drive = build('drive', 'v3', credentials=creds)
    return docs, drive


def cmd_create(args):
    docs, _ = get_services()

    with open(args.file, 'r', encoding='utf-8') as f:
        content = f.read()

    title = args.title or os.path.splitext(os.path.basename(args.file))[0]

    doc = docs.documents().create(body={'title': title}).execute()
    doc_id = doc['documentId']

    if content.strip():
        requests = [{
            'insertText': {
                'location': {'index': 1},
                'text': content,
            }
        }]
        docs.documents().batchUpdate(
            documentId=doc_id, body={'requests': requests}
        ).execute()

    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"Created: {title}")
    print(f"URL: {url}")
    print(f"ID: {doc_id}")


def cmd_update(args):
    docs, _ = get_services()
    doc_id = extract_doc_id(args.doc)

    with open(args.file, 'r', encoding='utf-8') as f:
        content = f.read()

    doc = docs.documents().get(documentId=doc_id).execute()
    body_content = doc.get('body', {}).get('content', [])
    end_index = 1
    for el in body_content:
        if 'endIndex' in el:
            end_index = max(end_index, el['endIndex'])

    requests = []
    if end_index > 2:
        requests.append({
            'deleteContentRange': {
                'range': {
                    'startIndex': 1,
                    'endIndex': end_index - 1,
                }
            }
        })

    if content.strip():
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': content,
            }
        })

    if requests:
        docs.documents().batchUpdate(
            documentId=doc_id, body={'requests': requests}
        ).execute()

    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"Updated: {doc_id}")
    print(f"URL: {url}")


def cmd_find(args):
    _, drive = get_services()

    query = (
        f"mimeType='application/vnd.google-apps.document' and "
        f"name contains '{args.title}' and trashed=false"
    )
    results = drive.files().list(
        q=query,
        pageSize=20,
        fields='files(id, name, modifiedTime, webViewLink)',
    ).execute()

    files = results.get('files', [])
    if not files:
        print(f"No docs found matching: {args.title}")
        return

    for f in files:
        print(f"{f['name']}")
        print(f"  ID:  {f['id']}")
        print(f"  URL: {f['webViewLink']}")
        print(f"  Modified: {f['modifiedTime']}")
        print()


def cmd_read(args):
    docs, _ = get_services()
    doc_id = extract_doc_id(args.doc)

    doc = docs.documents().get(documentId=doc_id).execute()
    body_content = doc.get('body', {}).get('content', [])

    out = []
    for el in body_content:
        para = el.get('paragraph')
        if not para:
            continue
        for run in para.get('elements', []):
            text = run.get('textRun', {}).get('content', '')
            out.append(text)

    print(''.join(out))


def main():
    parser = argparse.ArgumentParser(description='Google Docs CLI')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_create = sub.add_parser('create', help='Create a new Google Doc from a file')
    p_create.add_argument('file', help='Path to text file')
    p_create.add_argument('--title', help='Doc title (defaults to filename)')
    p_create.set_defaults(func=cmd_create)

    p_update = sub.add_parser('update', help='Replace contents of an existing Doc')
    p_update.add_argument('doc', help='Doc ID or URL')
    p_update.add_argument('file', help='Path to text file')
    p_update.set_defaults(func=cmd_update)

    p_find = sub.add_parser('find', help='Find Docs by title substring')
    p_find.add_argument('title', help='Title or partial title')
    p_find.set_defaults(func=cmd_find)

    p_read = sub.add_parser('read', help='Print plain text of a Doc')
    p_read.add_argument('doc', help='Doc ID or URL')
    p_read.set_defaults(func=cmd_read)

    args = parser.parse_args()
    try:
        args.func(args)
    except HttpError as e:
        msg = str(e)
        if 'has not been used' in msg or 'is disabled' in msg:
            print("\nGoogle Docs API or Drive API not enabled in your Cloud project.")
            print("Enable here:")
            print("  https://console.developers.google.com/apis/api/docs.googleapis.com/overview")
            print("  https://console.developers.google.com/apis/api/drive.googleapis.com/overview")
            print("\nFull error:")
            print(msg)
            sys.exit(2)
        raise


if __name__ == '__main__':
    main()
