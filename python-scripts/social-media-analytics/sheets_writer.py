import os
import re
import gspread
from collections import defaultdict, Counter
from dotenv import load_dotenv
from datetime import datetime
from auth import get_credentials

load_dotenv()

SHARE_EMAIL = 'graydavis33@gmail.com'

# --- Formula injection protection ---
_FORMULA_CHARS = ('=', '+', '-', '@', '|', '\t', '\r')

def _safe(value):
    """Prevent Google Sheets formula injection by prefixing dangerous strings."""
    if isinstance(value, str) and value.startswith(_FORMULA_CHARS):
        return "'" + value
    return value


# --- Header definitions ---
# (Display label, video dict key, tooltip description)
# Use None as the field key for computed/timestamp fields.
HEADER_DEFS = [
    ('Platform',                'platform',              'Which platform this video is from (e.g. YouTube)'),
    ('Title',                   'title',                 'Video title'),
    ('URL',                     'url',                   'Direct link to the video'),
    ('Published Date',          'published_date',        'Date the video was first published'),
    ('Duration',                'duration',              'Video length (M:SS or H:MM:SS)'),
    ('Views',                   'views',                 'Total number of views all time'),
    ('Impressions',             'impressions',           'How many times your thumbnail was shown to potential viewers on YouTube'),
    ('CTR (%)',                 'ctr_pct',               'Click-Through Rate — % of impressions that led to a view'),
    ('Watch Time (min)',        'watch_time_minutes',    'Total minutes watched across all viewers combined'),
    ('Avg View Duration (sec)', 'avg_view_duration_sec', 'Average seconds a viewer watches before leaving'),
    ('Avg View (%)',            'avg_view_pct',          'Average % of the video viewers watch — key retention signal'),
    ('Likes',                   'likes',                 'Total likes received'),
    ('Comments',                'comments',              'Total number of comments left on this video'),
    ('Shares',                  'shares',                'Total number of times this video was shared'),
    ('Subscribers Gained',      'subscribers_gained',    'Net new subscribers attributed to this video'),
    ('Views Gained',            'views_gained',          'Views gained since the last script run'),
    ('Growth (%)',              'views_growth_pct',      '% view growth since the last script run'),
    ('Engagement Rate (%)',     'engagement_rate',       '(Likes + Comments + Shares) ÷ Views × 100'),
    ('Last Updated',            None,                    'When this row was last refreshed by the analytics script'),
]

HEADER_FIELD = {h: f for h, f, _ in HEADER_DEFS}
HEADER_NOTE  = {h: d for h, _, d in HEADER_DEFS}
ALL_HEADERS  = [h for h, _, _ in HEADER_DEFS]
SHORTS_HEADERS = [h for h in ALL_HEADERS if h not in ('Impressions', 'CTR (%)')]

TIKTOK_HEADERS = [
    'Platform', 'Title', 'URL', 'Published Date', 'Duration',
    'Views', 'Likes', 'Comments', 'Shares',
    'Views Gained', 'Growth (%)', 'Engagement Rate (%)', 'Last Updated',
]

INSTAGRAM_HEADERS = [
    'Platform', 'Title', 'URL', 'Published Date',
    'Views', 'Impressions', 'Likes', 'Comments', 'Shares', 'Saves',
    'Views Gained', 'Growth (%)', 'Engagement Rate (%)', 'Last Updated',
]

FACEBOOK_HEADERS = [
    'Platform', 'Title', 'URL', 'Published Date',
    'Views', 'Impressions', 'Likes', 'Comments', 'Shares',
    'Views Gained', 'Growth (%)', 'Engagement Rate (%)', 'Last Updated',
]

# 'Saves' is Instagram-specific — reuses the subscribers_gained field key
HEADER_FIELD['Saves'] = 'subscribers_gained'
HEADER_NOTE['Saves']  = 'Number of times this post was saved by users'

COMMENTS_HEADERS = ['Title', 'URL', 'Comment Count', 'AI Summary', 'Summary Generated At']
COMMENTS_NOTES = {
    'Title':                'Video title',
    'URL':                  'Direct link to the video',
    'Comment Count':        'Total number of comments on this video (updated every run)',
    'AI Summary':           'Claude AI-generated summary of comments — run comment_summarizer.py to generate',
    'Summary Generated At': 'When the AI comment summary was last generated',
}

_STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
    'with', 'by', 'is', 'it', 'this', 'that', 'my', 'i', 'how', 'what', 'why',
    'when', 'you', 'your', 'me', 'we', 'our', 'are', 'was', 'be', 'has', 'do',
    'did', 'not', 'so', 'if', 'as', 'from', 'its', 'into', 'get', 'got', 'just',
}


# --- Growth & engagement helpers ---

def _read_existing_views(spreadsheet, tab_name):
    """Read {url: view_count} from an existing tab before overwriting it."""
    try:
        ws = spreadsheet.worksheet(tab_name)
        data = ws.get_all_values()
        if len(data) < 2:
            return {}
        headers = data[0]
        if 'URL' not in headers or 'Views' not in headers:
            return {}
        url_col   = headers.index('URL')
        views_col = headers.index('Views')
        result = {}
        for row in data[1:]:
            if len(row) > max(url_col, views_col) and row[url_col]:
                try:
                    result[row[url_col]] = int(str(row[views_col]).replace(',', ''))
                except (ValueError, AttributeError):
                    pass
        return result
    except gspread.WorksheetNotFound:
        return {}


def _compute_video_fields(videos, prev_views):
    """Add engagement_rate, views_gained, views_growth_pct to each video dict in-place."""
    for v in videos:
        views = v.get('views', 0) or 1
        v['engagement_rate'] = round(
            (v.get('likes', 0) + v.get('comments', 0) + v.get('shares', 0)) / views * 100, 2
        )
        prev = prev_views.get(v['url'])
        if prev is not None:
            diff = v['views'] - prev
            v['views_gained']     = diff
            v['views_growth_pct'] = round(diff / prev * 100, 1) if prev > 0 else 0
        else:
            v['views_gained']     = ''
            v['views_growth_pct'] = ''


# --- Spreadsheet / worksheet helpers ---

def get_spreadsheet(gc):
    sheet_id = os.getenv('SHEET_ID', '').strip()
    if sheet_id:
        try:
            return gc.open_by_key(sheet_id)
        except Exception as e:
            print(f"Warning: Couldn't open sheet {sheet_id}: {type(e).__name__}")

    print("Creating new Google Sheet 'Social Media Analytics'...")
    spreadsheet = gc.create('Social Media Analytics')
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
        new_content = content.replace('SHEET_ID=', f'SHEET_ID={spreadsheet.id}')
        tmp = env_path + '.tmp'
        with open(tmp, 'w') as f:
            f.write(new_content)
        os.replace(tmp, env_path)  # atomic write
    print(f"Sheet created: {spreadsheet.url}")
    return spreadsheet


def get_or_create_worksheet(spreadsheet, tab_name, headers):
    try:
        ws = spreadsheet.worksheet(tab_name)
        if ws.row_values(1) != headers:
            ws.update('A1', [headers])  # overwrite header row (not insert, which duplicates it)
        return ws, False
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(tab_name, rows=2000, cols=max(len(headers), 10))
        ws.update('A1', [headers])
        for name in ['Sheet1', 'Sheet 1']:
            try:
                spreadsheet.del_worksheet(spreadsheet.worksheet(name))
                break
            except Exception:
                pass
        return ws, True


def apply_formatting(spreadsheet, ws, num_cols):
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
                        'endColumnIndex': num_cols
                    }
                }
            }
        }
    ]})


def add_header_notes(spreadsheet, ws, headers, extra_notes=None):
    note_map = {**HEADER_NOTE, **(extra_notes or {})}
    requests = []
    for col_idx, h in enumerate(headers):
        note = note_map.get(h, '')
        if note:
            requests.append({
                'updateCells': {
                    'rows': [{'values': [{'note': note}]}],
                    'fields': 'note',
                    'range': {
                        'sheetId': ws.id,
                        'startRowIndex': 0, 'endRowIndex': 1,
                        'startColumnIndex': col_idx, 'endColumnIndex': col_idx + 1,
                    }
                }
            })
    if requests:
        try:
            spreadsheet.batch_update({'requests': requests})
        except Exception as e:
            print(f"Note: Could not add header tooltips: {type(e).__name__}")


def _bold_rows(spreadsheet, ws, row_indices, num_cols):
    """Apply bold formatting to specified rows (0-indexed)."""
    requests = [
        {
            'repeatCell': {
                'range': {
                    'sheetId': ws.id,
                    'startRowIndex': idx,
                    'endRowIndex': idx + 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': num_cols,
                },
                'cell': {'userEnteredFormat': {'textFormat': {'bold': True}}},
                'fields': 'userEnteredFormat.textFormat.bold',
            }
        }
        for idx in row_indices
    ]
    if requests:
        try:
            spreadsheet.batch_update({'requests': requests})
        except Exception:
            pass


def _autoresize(spreadsheet, ws, num_cols):
    spreadsheet.batch_update({'requests': [{'autoResizeDimensions': {
        'dimensions': {
            'sheetId': ws.id,
            'dimension': 'COLUMNS',
            'startIndex': 0,
            'endIndex': num_cols,
        }
    }}]})


# --- Row builder ---

def build_row(v, headers, now):
    row = []
    for h in headers:
        field = HEADER_FIELD.get(h)
        val = now if field is None else v.get(field, '')
        row.append(_safe(val))
    return row


# --- Tab writers ---

def smart_write(spreadsheet, ws, videos, headers, label):
    """Update existing rows by URL, append new ones."""
    url_col = headers.index('URL')
    existing_data = ws.get_all_values()

    existing_map = {}
    if len(existing_data) > 1:
        for i, row in enumerate(existing_data[1:], start=2):
            if len(row) > url_col and row[url_col]:
                existing_map[row[url_col]] = i

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    to_update, to_append = [], []

    for v in videos:
        row_data = build_row(v, headers, now)
        if v['url'] in existing_map:
            to_update.append((existing_map[v['url']], row_data))
        else:
            to_append.append(row_data)

    if to_update:
        ws.batch_update([{'range': f'A{row_num}', 'values': [row_data]}
                         for row_num, row_data in to_update])
    if to_append:
        ws.append_rows(to_append)

    _autoresize(spreadsheet, ws, len(headers))
    print(f"{label}: {len(to_update)} updated, {len(to_append)} new.")


def write_comments_tab(spreadsheet, videos):
    ws, created = get_or_create_worksheet(spreadsheet, 'Comments', COMMENTS_HEADERS)
    apply_formatting(spreadsheet, ws, len(COMMENTS_HEADERS))
    if created:
        add_header_notes(spreadsheet, ws, COMMENTS_HEADERS, COMMENTS_NOTES)

    url_col_idx   = COMMENTS_HEADERS.index('URL')
    count_col_idx = COMMENTS_HEADERS.index('Comment Count')
    title_col_idx = COMMENTS_HEADERS.index('Title')

    existing_data = ws.get_all_values()
    existing_map = {}
    if len(existing_data) > 1:
        for i, row in enumerate(existing_data[1:], start=2):
            if len(row) > url_col_idx and row[url_col_idx]:
                existing_map[row[url_col_idx]] = (i, row)

    to_update, to_append = [], []
    for v in videos:
        url   = _safe(v['url'])
        title = _safe(v['title'])
        if url in existing_map:
            row_num, existing_row = existing_map[url]
            new_row = list(existing_row) + [''] * (len(COMMENTS_HEADERS) - len(existing_row))
            new_row[title_col_idx] = title
            new_row[url_col_idx]   = url
            new_row[count_col_idx] = v['comments']
            to_update.append((row_num, new_row))
        else:
            new_row = [''] * len(COMMENTS_HEADERS)
            new_row[title_col_idx] = title
            new_row[url_col_idx]   = url
            new_row[count_col_idx] = v['comments']
            to_append.append(new_row)

    if to_update:
        ws.batch_update([{'range': f'A{row_num}', 'values': [row_data]}
                         for row_num, row_data in to_update])
    if to_append:
        ws.append_rows(to_append)

    _autoresize(spreadsheet, ws, len(COMMENTS_HEADERS))
    print(f"Comments: {len(to_update)} updated, {len(to_append)} new.")


def write_dashboard_tab(spreadsheet, videos, ai_summary=''):
    """Write a channel overview dashboard — all platforms."""
    if not videos:
        return

    now      = datetime.now().strftime('%Y-%m-%d %H:%M')
    num_cols = 7

    # Group by platform
    platform_groups = defaultdict(list)
    for v in videos:
        platform_groups[v.get('platform', 'Unknown')].append(v)

    top5    = sorted(videos, key=lambda x: x['views'], reverse=True)[:5]
    bottom5 = sorted(videos, key=lambda x: x['views'])[:5]

    rows      = []
    bold_idxs = []  # 0-indexed row positions to bold

    def add_bold_row(label):
        bold_idxs.append(len(rows))
        rows.append([label, '', '', '', '', '', ''])

    rows.append(['Channel Dashboard', '', '', '', '', '', ''])
    rows.append(['Last Updated:', now, '', '', '', '', ''])
    rows.append(['', '', '', '', '', '', ''])

    add_bold_row('OVERVIEW BY PLATFORM')
    bold_idxs.append(len(rows))  # column header row
    rows.append(['Platform', 'Videos', 'Total Views', 'Watch Time (min)',
                 'Avg CTR (%)', 'Avg View (%)', 'Avg Engagement (%)'])

    for platform, vids in sorted(platform_groups.items()):
        n = len(vids)
        rows.append([
            platform,
            n,
            sum(v['views'] for v in vids),
            round(sum(v['watch_time_minutes'] for v in vids)),
            round(sum(v['ctr_pct'] for v in vids) / n, 2) if n else 0,
            round(sum(v['avg_view_pct'] for v in vids) / n, 1) if n else 0,
            round(sum(v.get('engagement_rate', 0) for v in vids) / n, 2) if n else 0,
        ])

    rows.append(['', '', '', '', '', '', ''])

    if ai_summary:
        add_bold_row('AI CHANNEL SUMMARY')
        rows.append([ai_summary, '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', ''])

    add_bold_row('TOP 5 VIDEOS BY VIEWS')
    bold_idxs.append(len(rows))
    rows.append(['Title', 'Views', 'CTR (%)', 'Avg View (%)', 'Engagement (%)', 'Published', ''])
    for v in top5:
        rows.append([_safe(v['title']), v['views'], v['ctr_pct'],
                     v['avg_view_pct'], v.get('engagement_rate', ''), v['published_date'], ''])

    rows.append(['', '', '', '', '', '', ''])

    add_bold_row('BOTTOM 5 VIDEOS BY VIEWS')
    bold_idxs.append(len(rows))
    rows.append(['Title', 'Views', 'CTR (%)', 'Avg View (%)', 'Engagement (%)', 'Published', ''])
    for v in bottom5:
        rows.append([_safe(v['title']), v['views'], v['ctr_pct'],
                     v['avg_view_pct'], v.get('engagement_rate', ''), v['published_date'], ''])

    # Write to sheet (clear + rewrite each run)
    try:
        ws = spreadsheet.worksheet('Dashboard')
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet('Dashboard', rows=200, cols=num_cols)
        for name in ['Sheet1', 'Sheet 1']:
            try:
                spreadsheet.del_worksheet(spreadsheet.worksheet(name))
                break
            except Exception:
                pass

    ws.update('A1', rows)
    _bold_rows(spreadsheet, ws, bold_idxs, num_cols)
    _autoresize(spreadsheet, ws, num_cols)

    # Move Dashboard to the first tab position
    try:
        spreadsheet.batch_update({'requests': [{
            'updateSheetProperties': {
                'properties': {'sheetId': ws.id, 'index': 0},
                'fields': 'index'
            }
        }]})
    except Exception:
        pass

    print("Dashboard tab updated.")


def write_posting_day_tab(spreadsheet, videos):
    """Write best posting day analysis grouped by platform and day of week."""
    if not videos:
        return

    DAYS    = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    headers = ['Platform', 'Day', 'Videos Posted', 'Avg Views',
               'Avg CTR (%)', 'Avg View (%)', 'Avg Engagement (%)']

    ws, created = get_or_create_worksheet(spreadsheet, 'Best Posting Day', headers)
    apply_formatting(spreadsheet, ws, len(headers))

    groups = defaultdict(list)
    for v in videos:
        try:
            day = datetime.strptime(v['published_date'], '%Y-%m-%d').strftime('%A')
            groups[(v.get('platform', 'Unknown'), day)].append(v)
        except Exception:
            pass

    platforms = sorted(set(v.get('platform', 'Unknown') for v in videos))
    data_rows = []
    for platform in platforms:
        for day in DAYS:
            vids  = groups.get((platform, day), [])
            count = len(vids)
            if count > 0:
                avg_views = round(sum(v['views'] for v in vids) / count)
                avg_ctr   = round(sum(v['ctr_pct'] for v in vids) / count, 2)
                avg_vp    = round(sum(v['avg_view_pct'] for v in vids) / count, 1)
                avg_eng   = round(sum(v.get('engagement_rate', 0) for v in vids) / count, 2)
            else:
                avg_views = avg_ctr = avg_vp = avg_eng = 0
            data_rows.append([platform, day, count, avg_views, avg_ctr, avg_vp, avg_eng])

    if data_rows:
        ws.batch_clear(['A2:G1000'])
        ws.update('A2', data_rows)
        _autoresize(spreadsheet, ws, len(headers))

    print("Best Posting Day tab updated.")


def write_title_analysis_tab(spreadsheet, videos, ai_analysis=''):
    """Write title word frequency analysis for YouTube videos."""
    yt_videos = [v for v in videos if v.get('platform') == 'YouTube']
    if len(yt_videos) < 4:
        return

    sorted_vids = sorted(yt_videos, key=lambda v: v['views'], reverse=True)
    split       = max(5, len(sorted_vids) // 4)
    top_vids    = sorted_vids[:split]
    bottom_vids = sorted_vids[-split:]

    def get_words(vid_list):
        words = []
        for v in vid_list:
            words.extend(re.findall(r'\b[a-zA-Z]{3,}\b', v['title'].lower()))
        return Counter(w for w in words if w not in _STOP_WORDS)

    top_words    = get_words(top_vids).most_common(20)
    bottom_words = get_words(bottom_vids).most_common(20)

    headers = ['Top Performer Words', 'Count', '', 'Low Performer Words', 'Count']
    ws, created = get_or_create_worksheet(spreadsheet, 'Title Analysis', headers)
    apply_formatting(spreadsheet, ws, len(headers))

    word_rows  = []
    bold_idxs  = []  # sheet row indices (0-based) to bold

    for i in range(max(len(top_words), len(bottom_words))):
        tw, tc = top_words[i]    if i < len(top_words)    else ('', '')
        bw, bc = bottom_words[i] if i < len(bottom_words) else ('', '')
        word_rows.append([tw, tc, '', bw, bc])

    if ai_analysis:
        word_rows.append(['', '', '', '', ''])
        ai_header_pos = len(word_rows)  # position in word_rows (0-based)
        word_rows.append(['AI TITLE INSIGHTS', '', '', '', ''])
        for line in ai_analysis.split('\n'):
            if line.strip():
                word_rows.append([line.strip(), '', '', '', ''])
        # sheet row index = ai_header_pos + 1 (header row is index 0)
        bold_idxs.append(ai_header_pos + 1)

    if word_rows:
        ws.batch_clear(['A2:E1000'])
        ws.update('A2', word_rows)
        if bold_idxs:
            _bold_rows(spreadsheet, ws, bold_idxs, len(headers))
        _autoresize(spreadsheet, ws, len(headers))

    print("Title Analysis tab updated.")


# --- Main entry point ---

def write_video_data(videos, ai_insights=None):
    """Write all video data to Google Sheets.
    Platform-agnostic: pass videos from YouTube, TikTok, Instagram, etc.
    Each video dict must have a 'platform' field."""
    creds = get_credentials()
    gc    = gspread.authorize(creds)
    spreadsheet = get_spreadsheet(gc)

    try:
        spreadsheet.share(SHARE_EMAIL, perm_type='user', role='writer', notify=False)
    except Exception as e:
        print(f"Note: Could not share with {SHARE_EMAIL}: {type(e).__name__}")

    # Read old view counts BEFORE overwriting (needed for growth computation)
    prev_views = {
        **_read_existing_views(spreadsheet, 'YouTube Shorts'),
        **_read_existing_views(spreadsheet, 'YouTube Longform'),
        **_read_existing_views(spreadsheet, 'TikTok'),
        **_read_existing_views(spreadsheet, 'Instagram'),
        **_read_existing_views(spreadsheet, 'Facebook'),
    }

    # Enrich all video dicts with engagement rate + growth fields
    _compute_video_fields(videos, prev_views)

    ai_insights = ai_insights or {}

    # YouTube-specific splits
    shorts   = [v for v in videos if v.get('platform') == 'YouTube' and v.get('is_short')]
    longform = [v for v in videos if v.get('platform') == 'YouTube' and not v.get('is_short')]

    # Dashboard first so it becomes the leftmost tab on first run
    write_dashboard_tab(spreadsheet, videos, ai_insights.get('dashboard', ''))

    # YouTube Shorts
    ws_shorts, created = get_or_create_worksheet(spreadsheet, 'YouTube Shorts', SHORTS_HEADERS)
    apply_formatting(spreadsheet, ws_shorts, len(SHORTS_HEADERS))
    if created:
        add_header_notes(spreadsheet, ws_shorts, SHORTS_HEADERS)
    if shorts:
        smart_write(spreadsheet, ws_shorts, shorts, SHORTS_HEADERS, 'YouTube Shorts')
    else:
        print("YouTube Shorts: no Shorts detected yet.")

    # YouTube Longform
    ws_long, created = get_or_create_worksheet(spreadsheet, 'YouTube Longform', ALL_HEADERS)
    apply_formatting(spreadsheet, ws_long, len(ALL_HEADERS))
    if created:
        add_header_notes(spreadsheet, ws_long, ALL_HEADERS)
    if longform:
        smart_write(spreadsheet, ws_long, longform, ALL_HEADERS, 'YouTube Longform')
    else:
        print("YouTube Longform: tab ready, no longform videos yet.")

    # TikTok
    tiktok_videos = [v for v in videos if v.get('platform') == 'TikTok']
    if tiktok_videos:
        ws_tt, created = get_or_create_worksheet(spreadsheet, 'TikTok', TIKTOK_HEADERS)
        apply_formatting(spreadsheet, ws_tt, len(TIKTOK_HEADERS))
        if created:
            add_header_notes(spreadsheet, ws_tt, TIKTOK_HEADERS)
        smart_write(spreadsheet, ws_tt, tiktok_videos, TIKTOK_HEADERS, 'TikTok')

    # Instagram
    ig_videos = [v for v in videos if v.get('platform') == 'Instagram']
    if ig_videos:
        ws_ig, created = get_or_create_worksheet(spreadsheet, 'Instagram', INSTAGRAM_HEADERS)
        apply_formatting(spreadsheet, ws_ig, len(INSTAGRAM_HEADERS))
        if created:
            add_header_notes(spreadsheet, ws_ig, INSTAGRAM_HEADERS)
        smart_write(spreadsheet, ws_ig, ig_videos, INSTAGRAM_HEADERS, 'Instagram')

    # Facebook
    fb_videos = [v for v in videos if v.get('platform') == 'Facebook']
    if fb_videos:
        ws_fb, created = get_or_create_worksheet(spreadsheet, 'Facebook', FACEBOOK_HEADERS)
        apply_formatting(spreadsheet, ws_fb, len(FACEBOOK_HEADERS))
        if created:
            add_header_notes(spreadsheet, ws_fb, FACEBOOK_HEADERS)
        smart_write(spreadsheet, ws_fb, fb_videos, FACEBOOK_HEADERS, 'Facebook')

    # Comments
    write_comments_tab(spreadsheet, videos)

    # Best Posting Day (all platforms)
    write_posting_day_tab(spreadsheet, videos)

    # Title Analysis (YouTube only for now)
    write_title_analysis_tab(spreadsheet, videos, ai_insights.get('title', ''))

    return spreadsheet
