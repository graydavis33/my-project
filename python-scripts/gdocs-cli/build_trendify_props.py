"""build_trendify_props.py - one-off script.

Creates the Trendify Props Doc in the karramedia.com Drive:
- 9 pages, one per word
- Each page: large centered icon + title (Montserrat Semi-Bold, Trendify orange, ALL CAPS)
- Trendify logo as the page footer (centered, small) on every page

Run once: `python build_trendify_props.py`
"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image
from auth import get_credentials


MAX_PIXELS_LONG_SIDE = 2000  # Docs API rejects very large images


def downsize_if_needed(src_path):
    """If the image's long side is bigger than the cap, write a resized copy
    into the same folder and return its path. Otherwise return src_path."""
    img = Image.open(src_path)
    w, h = img.size
    long_side = max(w, h)
    if long_side <= MAX_PIXELS_LONG_SIDE:
        return src_path
    scale = MAX_PIXELS_LONG_SIDE / long_side
    new_size = (int(w * scale), int(h * scale))
    base, ext = os.path.splitext(src_path)
    out = f'{base}.resized{ext}'
    img.resize(new_size, Image.LANCZOS).save(out)
    print(f'  resized {os.path.basename(src_path)}: {w}x{h} -> {new_size[0]}x{new_size[1]}')
    return out

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(HERE, 'icons')
LOGO_PATH = os.path.normpath(os.path.join(HERE, '..', '..', 'business', 'trendify-logo.png'))

PAGES = [
    ('01-how-we-got-here.png',     'HOW WE GOT HERE'),
    ('02-what-we-do.png',          'WHAT WE DO'),
    ('03-trendify-vision.png',     'TRENDIFY VISION'),
    ('04-how-we-communicate.png',  'HOW WE COMMUNICATE'),
    ('05-tools-that-we-use.png',   'TOOLS THAT WE USE'),
    ('06-housekeeping.png',        'HOUSEKEEPING'),
    ('07-keep-things-safe.png',    'KEEP THINGS SAFE'),
    ('08-key-terms-to-know.png',   'KEY TERMS TO KNOW'),
    ('09-core-values.png',         'CORE VALUES'),
]

ORANGE_RGB = {'red': 242 / 255, 'green': 129 / 255, 'blue': 41 / 255}
DOC_TITLE = 'Trendify Props - Title Pages'

ICON_SIZE_PT = 80      # ~1.1 inches square (quarter of original 320)
TITLE_PT = 18          # ~0.25 inches tall caps (quarter of original 72)
LOGO_FOOTER_W_PT = 110
LOGO_FOOTER_H_PT = 30  # ~3.7:1 aspect to match the trendify logo


def upload_image(drive, path, name):
    """Upload PNG to Drive, make anyone-with-link viewer, return embed URL.
    Auto-downsizes if dimensions exceed the Docs API limit."""
    upload_path = downsize_if_needed(path)
    media = MediaFileUpload(upload_path, mimetype='image/png')
    f = drive.files().create(
        body={'name': name},
        media_body=media,
        fields='id',
    ).execute()
    fid = f['id']
    drive.permissions().create(
        fileId=fid,
        body={'role': 'reader', 'type': 'anyone'},
    ).execute()
    return f'https://drive.google.com/uc?export=view&id={fid}', fid


def get_body_end(docs, doc_id):
    """Return the index just before the body's final trailing newline."""
    d = docs.documents().get(documentId=doc_id).execute()
    end = 1
    for el in d.get('body', {}).get('content', []):
        if 'endIndex' in el:
            end = max(end, el['endIndex'])
    return end - 1


def main():
    creds = get_credentials()
    docs = build('docs', 'v1', credentials=creds)
    drive = build('drive', 'v3', credentials=creds)

    print('Uploading icons + logo to Drive...')
    image_urls = {}
    for filename, _ in PAGES:
        url, fid = upload_image(drive, os.path.join(ICONS_DIR, filename), f'trendify-prop-{filename}')
        image_urls[filename] = url
        print(f'  {filename} -> {fid}')

    logo_url, logo_id = upload_image(drive, LOGO_PATH, 'trendify-prop-logo.png')
    print(f'  logo -> {logo_id}')

    print('\nCreating doc...')
    doc = docs.documents().create(body={'title': DOC_TITLE}).execute()
    doc_id = doc['documentId']
    print(f'  doc id: {doc_id}')

    print('Creating footer with Trendify logo...')
    resp = docs.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': [{'createFooter': {'type': 'DEFAULT'}}]},
    ).execute()
    footer_id = resp['replies'][0]['createFooter']['footerId']

    docs.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': [
            {
                'insertInlineImage': {
                    'location': {'segmentId': footer_id, 'index': 0},
                    'uri': logo_url,
                    'objectSize': {
                        'width':  {'magnitude': LOGO_FOOTER_W_PT, 'unit': 'PT'},
                        'height': {'magnitude': LOGO_FOOTER_H_PT, 'unit': 'PT'},
                    },
                },
            },
            {
                'updateParagraphStyle': {
                    'range': {'segmentId': footer_id, 'startIndex': 0, 'endIndex': 1},
                    'paragraphStyle': {'alignment': 'CENTER'},
                    'fields': 'alignment',
                },
            },
        ]},
    ).execute()

    print('\nBuilding pages...')
    for i, (filename, title) in enumerate(PAGES):
        is_last = (i == len(PAGES) - 1)
        insert_at = get_body_end(docs, doc_id)
        print(f'  Page {i+1} (idx {insert_at}): {title}')

        requests = [
            # 1. Image
            {
                'insertInlineImage': {
                    'location': {'index': insert_at},
                    'uri': image_urls[filename],
                    'objectSize': {
                        'width':  {'magnitude': ICON_SIZE_PT, 'unit': 'PT'},
                        'height': {'magnitude': ICON_SIZE_PT, 'unit': 'PT'},
                    },
                },
            },
            # 2. Newline + title + newline
            {
                'insertText': {
                    'location': {'index': insert_at + 1},
                    'text': '\n' + title + '\n',
                },
            },
        ]

        # After both inserts:
        #   insert_at:                                  image (1 char)
        #   insert_at + 1:                              \n  (start of inserted text)
        #   insert_at + 2 .. + 1 + len(title):          title characters
        #   insert_at + 2 + len(title):                 \n  (end of inserted text)
        title_start = insert_at + 2
        title_end_excl = title_start + len(title)

        # 3. Center the image paragraph
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': insert_at, 'endIndex': insert_at + 1},
                'paragraphStyle': {'alignment': 'CENTER'},
                'fields': 'alignment',
            },
        })

        # 4. Style title text
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': title_start, 'endIndex': title_end_excl},
                'textStyle': {
                    'weightedFontFamily': {'fontFamily': 'Montserrat', 'weight': 600},
                    'fontSize': {'magnitude': TITLE_PT, 'unit': 'PT'},
                    'foregroundColor': {'color': {'rgbColor': ORANGE_RGB}},
                },
                'fields': 'weightedFontFamily,fontSize,foregroundColor',
            },
        })

        # 5. Center title paragraph
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': title_start, 'endIndex': title_end_excl + 1},
                'paragraphStyle': {'alignment': 'CENTER'},
                'fields': 'alignment',
            },
        })

        # 6. Page break (skip after last page)
        if not is_last:
            requests.append({
                'insertPageBreak': {'location': {'index': title_end_excl + 1}},
            })

        docs.documents().batchUpdate(
            documentId=doc_id, body={'requests': requests},
        ).execute()

    url = f'https://docs.google.com/document/d/{doc_id}/edit'
    print(f'\nDone!')
    print(f'URL: {url}')


if __name__ == '__main__':
    main()
