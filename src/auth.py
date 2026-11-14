"""Small server-side authentication service for the local screening application."""

import hashlib
import hmac
import os
import secrets
import sqlite3
from pathlib import Path

AUTH_DB = Path(os.getenv("AUTH_DB_PATH", Path(__file__).resolve().parent.parent / "data" / "auth.sqlite3"))
SESSION_COOKIE = "smart_health_session"
SESSION_DAYS = 7


def _connection():
    AUTH_DB.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(AUTH_DB)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_auth():
    with _connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL
            );
            """
        )


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 300_000)
    return f"{salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    salt_hex, digest = stored.split("$", 1)
    candidate = _hash_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
    return hmac.compare_digest(candidate, digest)


def create_user(name: str, email: str, password: str):
    try:
        with _connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users(name, email, password_hash) VALUES (?, ?, ?)",
                (name.strip(), email.strip().lower(), _hash_password(password)),
            )
            return {"id": cursor.lastrowid, "name": name.strip(), "email": email.strip().lower()}
    except sqlite3.IntegrityError as exc:
        raise ValueError("An account with this email already exists.") from exc


def authenticate(email: str, password: str):
    with _connection() as connection:
        user = connection.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    if not user or not _verify_password(password, user["password_hash"]):
        raise ValueError("Invalid email or password.")
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with _connection() as connection:
        connection.execute(
            "INSERT INTO sessions(token_hash, user_id, expires_at) VALUES (?, ?, datetime('now', '+7 days'))",
            (token_hash, user_id),
        )
    return token


def get_user(token: str | None):
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with _connection() as connection:
        user = connection.execute(
            """SELECT users.id, users.name, users.email FROM sessions
               JOIN users ON users.id = sessions.user_id
               WHERE sessions.token_hash = ? AND sessions.expires_at > CURRENT_TIMESTAMP""",
            (token_hash,),
        ).fetchone()
    return dict(user) if user else None


def delete_session(token: str | None):
    if token:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with _connection() as connection:
            connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))