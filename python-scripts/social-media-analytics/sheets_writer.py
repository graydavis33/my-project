import os
import gspread
from dotenv import load_dotenv
from datetime import datetime
from auth import get_credentials

load_dotenv()

LONGFORM_SECONDS = 600  # 10 minutes

HEADERS = [
    'Platform', 'Title', 'URL', 'Published Date',
    'Duration', 'Views', 'Impressions', 'CTR (%)',
    'Watch Time (min)', 'Avg View Duration (sec)', 'Avg View (%)',
    'Likes', 'Comments', 'Shares', 'Subscribers Gained', 'Last Updated'
]

# Match existing rows by URL (unique, stable, contains video ID)
URL_COL = HEADERS.index('URL')


def get_spreadsheet(gc):
    sheet_id = os.getenv('SHEET_ID', '').strip()
    if sheet_id:
        try:
            return gc.open_by_key(sheet_id)
        except Exception as e:
            print(f"Warning: Couldn't open sheet {sheet_id}: {e}")

    print("Creating new Google Sheet 'Social Media Analytics'...")
    spreadsheet = gc.create('Social Media Analytics')
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
        content = content.replace('SHEET_ID=', f'SHEET_ID={spreadsheet.id}')
        with open(env_path, 'w') as f:
            f.write(content)
    print(f"Sheet created: {spreadsheet.url}")
    return spreadsheet


def get_or_create_worksheet(spreadsheet, tab_name):
    try:
        return spreadsheet.worksheet(tab_name), False
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(tab_name, rows=2000, cols=len(HEADERS))
        ws.update('A1', [HEADERS])
        for name in ['Sheet1', 'Sheet 1']:
            try:
                spreadsheet.del_worksheet(spreadsheet.worksheet(name))
                break
            except Exception:
                pass
        return ws, True


def apply_formatting(spreadsheet, ws):
    try:
        spreadsheet.batch_update({'requests': [{'clearBasicFilter': {'sheetId': ws.id}}]})
    except Exception:
        pass

    spreadsheet.batch_update({'requests': [
        {
            'updateSheetProperties': {
                'properties': {
                    'sheetId': ws.id,
                    'gridProperties': {'frozenRowCount': 1}
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        },
        {
            'setBasicFilter': {
                'filter': {
                    'range': {
                        'sheetId': ws.id,
                        'startRowIndex': 0,
                        'startColumnIndex': 0,
                        'endColumnIndex': len(HEADERS)
                    }
                }
            }
        }
    ]})


def build_row(v, now):
    return [
        v['platform'], v['title'], v['url'],
        v['published_date'], v['duration'],
        v['views'], v['impressions'], v['ctr_pct'],
        v['watch_time_minutes'], v['avg_view_duration_sec'], v['avg_view_pct'],
        v['likes'], v['comments'], v['shares'], v['subscribers_gained'],
        now,
    ]


def smart_write(spreadsheet, ws, videos, label):
    """Update existing rows in place by matching URL. Append new videos only."""
    existing_data = ws.get_all_values()

    existing_map = {}  # url -> row number
    if len(existing_data) > 1:
        for i, row in enumerate(existing_data[1:], start=2):
            if len(row) > URL_COL and row[URL_COL]:
                existing_map[row[URL_COL]] = i

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    to_update = []
    to_append = []

    for v in videos:
        row_data = build_row(v, now)
        if v['url'] in existing_map:
            to_update.append((existing_map[v['url']], row_data))
        else:
            to_append.append(row_data)

    for row_num, row_data in to_update:
        ws.update(f'A{row_num}', [row_data])

    if to_append:
        ws.append_rows(to_append)

    spreadsheet.batch_update({'requests': [{
        'autoResizeDimensions': {
            'dimensions': {
                'sheetId': ws.id,
                'dimension': 'COLUMNS',
                'startIndex': 0,
                'endIndex': len(HEADERS)
            }
        }
    }]})

    print(f"{label}: {len(to_update)} updated, {len(to_append)} new.")


def write_youtube_data(videos):
    creds = get_credentials()
    gc = gspread.authorize(creds)
    spreadsheet = get_spreadsheet(gc)

    # All public YouTube videos
    ws_all, _ = get_or_create_worksheet(spreadsheet, 'YouTube')
    apply_formatting(spreadsheet, ws_all)
    smart_write(spreadsheet, ws_all, videos, 'YouTube')

    # Longform tab (>= 10 minutes)
    longform = [v for v in videos if v['duration_seconds'] >= LONGFORM_SECONDS]
    if longform:
        ws_long, _ = get_or_create_worksheet(spreadsheet, 'YouTube Longform')
        apply_formatting(spreadsheet, ws_long)
        smart_write(spreadsheet, ws_long, longform, 'YouTube Longform')
        print(f"Longform videos (>= 10 min): {len(longform)}")
    else:
        print("No longform videos found yet (>= 10 min).")

    return spreadsheet
