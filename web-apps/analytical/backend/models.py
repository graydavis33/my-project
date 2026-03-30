"""
SQL helpers for working with the database tables.
All queries use plain psycopg2 — no ORM.
"""
import json
from datetime import datetime, timezone


# ─── Users ───────────────────────────────────────────────────

def create_user(conn, email, password_hash):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id, email, tier, created_at",
            (email, password_hash)
        )
        conn.commit()
        return dict(cur.fetchone())


def get_user_by_email(conn, email):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_user_by_id(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("SELECT id, email, tier, stripe_customer_id, created_at FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def update_user_tier(conn, user_id, tier):
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET tier = %s WHERE id = %s", (tier, user_id))
        conn.commit()


def update_stripe_customer(conn, user_id, customer_id):
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET stripe_customer_id = %s WHERE id = %s", (customer_id, user_id))
        conn.commit()


def get_user_by_stripe_customer(conn, customer_id):
    with conn.cursor() as cur:
        cur.execute("SELECT id, email, tier FROM users WHERE stripe_customer_id = %s", (customer_id,))
        row = cur.fetchone()
        return dict(row) if row else None


# ─── Platform Connections ─────────────────────────────────────

def upsert_connection(conn, user_id, platform, access_token, refresh_token=None, expires_at=None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO platform_connections (user_id, platform, access_token, refresh_token, expires_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, platform)
            DO UPDATE SET
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                expires_at = EXCLUDED.expires_at,
                connected_at = NOW()
        """, (user_id, platform, access_token, refresh_token, expires_at))
        conn.commit()


def get_connection(conn, user_id, platform):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM platform_connections WHERE user_id = %s AND platform = %s",
            (user_id, platform)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_all_connections(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM platform_connections WHERE user_id = %s", (user_id,))
        return {row['platform']: dict(row) for row in cur.fetchall()}


def delete_connection(conn, user_id, platform):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM platform_connections WHERE user_id = %s AND platform = %s",
            (user_id, platform)
        )
        conn.commit()


# ─── Analytics Snapshots ─────────────────────────────────────

def save_snapshot(conn, user_id, platform, data):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO analytics_snapshots (user_id, platform, data) VALUES (%s, %s, %s)",
            (user_id, platform, json.dumps(data))
        )
        conn.commit()


def get_latest_snapshot(conn, user_id, platform):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT * FROM analytics_snapshots
            WHERE user_id = %s AND platform = %s
            ORDER BY fetched_at DESC
            LIMIT 1
        """, (user_id, platform))
        row = cur.fetchone()
        return dict(row) if row else None


def is_snapshot_stale(snapshot, max_age_hours=24):
    """Returns True if the snapshot is older than max_age_hours."""
    if not snapshot:
        return True
    fetched_at = snapshot['fetched_at']
    if isinstance(fetched_at, str):
        fetched_at = datetime.fromisoformat(fetched_at)
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600
    return age > max_age_hours


# ─── AI Insights ─────────────────────────────────────────────

def save_insight(conn, user_id, content):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO ai_insights (user_id, content) VALUES (%s, %s)",
            (user_id, content)
        )
        conn.commit()


def get_latest_insight(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT * FROM ai_insights
            WHERE user_id = %s
            ORDER BY generated_at DESC
            LIMIT 1
        """, (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def is_insight_stale(insight, max_age_days=7):
    """Returns True if the insight is older than max_age_days."""
    if not insight:
        return True
    generated_at = insight['generated_at']
    if isinstance(generated_at, str):
        generated_at = datetime.fromisoformat(generated_at)
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - generated_at).total_seconds() / 86400
    return age > max_age_days
