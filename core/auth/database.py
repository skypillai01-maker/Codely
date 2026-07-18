import sqlite3
import logging
from datetime import datetime, timezone
from contextlib import contextmanager
from core.config import AUTH_DB_PATH, BASE_STORAGE_PATH

logger = logging.getLogger(__name__)

@contextmanager
def get_db():
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    import os
    os.makedirs(BASE_STORAGE_PATH, exist_ok=True)

    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                display_name TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS magic_tokens (
                token TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_magic_tokens_email ON magic_tokens(email)")

        logger.info(f"[AUTH] Database initialized at {AUTH_DB_PATH}")

def get_user_by_email(email: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

def create_user(email: str, display_name: str = None) -> dict:
    user_id = f"user_{email.split('@')[0]}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    now = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (user_id, email, display_name, created_at) VALUES (?, ?, ?, ?)",
            (user_id, email.lower(), display_name or email.split("@")[0], now)
        )

    logger.info(f"[AUTH] Created user {user_id} for email {email}")
    return get_user_by_email(email)

def update_last_login(user_id: str):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute("UPDATE users SET last_login = ? WHERE user_id = ?", (now, user_id))

def create_session(user_id: str, expires_at: str) -> str:
    import secrets
    session_id = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (session_id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, user_id, now, expires_at)
        )

    return session_id

def validate_session(session_id: str) -> dict | None:
    now = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        row = conn.execute("""
            SELECT s.*, u.email, u.display_name
            FROM sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.session_id = ? AND s.is_active = 1 AND s.expires_at > ?
        """, (session_id, now)).fetchone()

        return dict(row) if row else None

def revoke_session(session_id: str):
    with get_db() as conn:
        conn.execute("UPDATE sessions SET is_active = 0 WHERE session_id = ?", (session_id,))

def cleanup_expired_sessions():
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute("UPDATE sessions SET is_active = 0 WHERE expires_at < ?", (now,))
