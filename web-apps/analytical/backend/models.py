"""
SQL helpers — SQLite. All queries use ? placeholders.
"""
import json
from datetime import datetime, timezone


# ─── Users ───────────────────────────────────────────────────

def create_user(conn, email, password_hash):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password_hash) VALUES (?, ?)",
        (email, password_hash)
    )
    conn.commit()
    user_id = cur.lastrowid
    cur.execute("SELECT id, email, tier, created_at FROM users WHERE id = ?", (user_id,))
    return cur.fetchone()


def get_user_by_email(conn, email):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    return cur.fetchone()


def get_user_by_id(conn, user_id):
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, tier, stripe_customer_id, created_at FROM users WHERE id = ?",
        (user_id,)
    )
    return cur.fetchone()


def update_user_tier(conn, user_id, tier):
    cur = conn.cursor()
    cur.execute("UPDATE users SET tier = ? WHERE id = ?", (tier, user_id))
    conn.commit()


def update_stripe_customer(conn, user_id, customer_id):
    cur = conn.cursor()
    cur.execute("UPDATE users SET stripe_customer_id = ? WHERE id = ?", (customer_id, user_id))
    conn.commit()


def get_user_by_stripe_customer(conn, customer_id):
    cur = conn.cursor()
    cur.execute("SELECT id, email, tier FROM users WHERE stripe_customer_id = ?", (customer_id,))
    return cur.fetchone()


# ─── Platform Connections ─────────────────────────────────────

def upsert_connection(conn, user_id, platform, access_token, refresh_token=None, expires_at=None):
    cur = conn.cursor()
    expires_str = None
    if expires_at:
        expires_str = expires_at.isoformat() if hasattr(expires_at, 'isoformat') else str(expires_at)
    cur.execute("""
        INSERT INTO platform_connections (user_id, platform, access_token, refresh_token, expires_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, platform) DO UPDATE SET
            access_token = excluded.access_token,
            refresh_token = excluded.refresh_token,
            expires_at = excluded.expires_at,
            connected_at = datetime('now')
    """, (user_id, platform, access_token, refresh_token, expires_str))
    conn.commit()


def get_platform_connection(conn, user_id, platform):
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM platform_connections WHERE user_id = ? AND platform = ?",
        (user_id, platform)
    )
    return cur.fetchone()


def get_all_connections(conn, user_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM platform_connections WHERE user_id = ?", (user_id,))
    return {row['platform']: row for row in cur.fetchall()}


def delete_connection(conn, user_id, platform):
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM platform_connections WHERE user_id = ? AND platform = ?",
        (user_id, platform)
    )
    conn.commit()


# ─── Analytics Snapshots ─────────────────────────────────────

def save_snapshot(conn, user_id, platform, data):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO analytics_snapshots (user_id, platform, data) VALUES (?, ?, ?)",
        (user_id, platform, json.dumps(data))
    )
    conn.commit()


def get_latest_snapshot(conn, user_id, platform):
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM analytics_snapshots
        WHERE user_id = ? AND platform = ?
        ORDER BY fetched_at DESC
        LIMIT 1
    """, (user_id, platform))
    row = cur.fetchone()
    if row and isinstance(row.get('data'), str):
        row = dict(row)
        row['data'] = json.loads(row['data'])
    return row


def is_snapshot_stale(snapshot, max_age_hours=24):
    if not snapshot:
        return True
    fetched_at = snapshot['fetched_at']
    if isinstance(fetched_at, str):
        fetched_at = datetime.fromisoformat(fetched_at.replace('Z', '+00:00'))
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600
    return age > max_age_hours


# ─── AI Insights ─────────────────────────────────────────────

def save_insight(conn, user_id, content):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ai_insights (user_id, content) VALUES (?, ?)",
        (user_id, content)
    )
    conn.commit()


def get_latest_insight(conn, user_id):
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM ai_insights
        WHERE user_id = ?
        ORDER BY generated_at DESC
        LIMIT 1
    """, (user_id,))
    return cur.fetchone()


def is_insight_stale(insight, max_age_days=7):
    if not insight:
        return True
    generated_at = insight['generated_at']
    if isinstance(generated_at, str):
        generated_at = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - generated_at).total_seconds() / 86400
    return age > max_age_days
