import hashlib
import os
import secrets
import sqlite3
from datetime import datetime

from database import DATABASE_NAME, add_column_if_missing, create_database


DEFAULT_AGENT_ID = "ebl-support-agent"
DEFAULT_AGENT_NAME = "EBL Support Agent"
DEFAULT_AGENT_EMAIL = "support@ebl.com"
DEFAULT_AGENT_PASSWORD = "Ebl@12345"


def current_time_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def row_to_safe_agent(row):
    if not row:
        return None

    return {
        "agent_id": row["agent_id"],
        "name": row["name"],
        "email": row["email"],
        "is_active": bool(row["is_active"]),
        "is_available": bool(row["is_available"]),
    }


def hash_password(password, salt=""):
    normalized_password = password or ""
    normalized_salt = salt or secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        normalized_password.encode("utf-8"),
        normalized_salt.encode("utf-8"),
        100_000,
    ).hex()

    return normalized_salt, password_hash


def create_agent_database():
    create_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT UNIQUE,
            name TEXT,
            email TEXT UNIQUE,
            password_salt TEXT,
            password_hash TEXT,
            is_active INTEGER DEFAULT 1,
            is_available INTEGER DEFAULT 1,
            last_seen_at TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    add_column_if_missing(
        cursor,
        "support_agents",
        "is_available",
        "INTEGER DEFAULT 1",
    )
    add_column_if_missing(
        cursor,
        "support_agents",
        "last_seen_at",
        "TEXT",
    )

    connection.commit()
    connection.close()


def create_support_agent(agent_id, name, email, password, is_active=True, is_available=True):
    create_agent_database()

    now = current_time_string()
    salt, password_hash = hash_password(password)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO support_agents (
            agent_id,
            name,
            email,
            password_salt,
            password_hash,
            is_active,
            is_available,
            last_seen_at,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE((
            SELECT created_at FROM support_agents WHERE agent_id = ?
        ), ?), ?)
    """, (
        agent_id,
        name,
        email.lower().strip(),
        salt,
        password_hash,
        1 if is_active else 0,
        1 if is_available else 0,
        now,
        agent_id,
        now,
        now,
    ))

    connection.commit()
    connection.close()


def seed_default_agent():
    create_agent_database()

    default_email = os.getenv("EBL_DEFAULT_AGENT_EMAIL", DEFAULT_AGENT_EMAIL).lower().strip()
    default_password = os.getenv("EBL_DEFAULT_AGENT_PASSWORD", DEFAULT_AGENT_PASSWORD)
    default_name = os.getenv("EBL_DEFAULT_AGENT_NAME", DEFAULT_AGENT_NAME)
    now = current_time_string()
    salt, password_hash = hash_password(default_password)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT agent_id
        FROM support_agents
        WHERE agent_id = ?
    """, (DEFAULT_AGENT_ID,))
    default_agent = cursor.fetchone()

    if default_agent:
        cursor.execute("""
            UPDATE support_agents
            SET name = ?,
                email = ?,
                password_salt = ?,
                password_hash = ?,
                is_active = 1,
                updated_at = ?
            WHERE agent_id = ?
        """, (
            default_name,
            default_email,
            salt,
            password_hash,
            now,
            DEFAULT_AGENT_ID,
        ))
        connection.commit()
        connection.close()
        return

    connection.close()

    create_support_agent(
        agent_id=DEFAULT_AGENT_ID,
        name=default_name,
        email=default_email,
        password=default_password,
        is_active=True,
        is_available=True,
    )


def verify_agent_login(email, password):
    create_agent_database()

    normalized_email = (email or "").lower().strip()

    if not normalized_email or not password:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM support_agents
        WHERE lower(email) = ?
        AND is_active = 1
    """, (normalized_email,))

    agent = cursor.fetchone()
    connection.close()

    if not agent:
        return None

    _, candidate_hash = hash_password(password, agent["password_salt"])

    if not secrets.compare_digest(candidate_hash, agent["password_hash"]):
        return None

    return row_to_safe_agent(agent)


def get_agent_by_id(agent_id):
    create_agent_database()

    normalized_agent_id = (agent_id or "").strip()

    if not normalized_agent_id:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM support_agents
        WHERE agent_id = ?
    """, (normalized_agent_id,))

    agent = cursor.fetchone()
    connection.close()

    return row_to_safe_agent(agent)


def update_agent_availability(agent_id, is_available):
    create_agent_database()

    normalized_agent_id = (agent_id or "").strip()

    if not normalized_agent_id:
        return None

    now = current_time_string()
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE support_agents
        SET is_available = ?,
            last_seen_at = ?,
            updated_at = ?
        WHERE agent_id = ?
        AND is_active = 1
    """, (
        1 if is_available else 0,
        now,
        now,
        normalized_agent_id,
    ))

    connection.commit()

    cursor.execute("""
        SELECT *
        FROM support_agents
        WHERE agent_id = ?
    """, (normalized_agent_id,))

    agent = cursor.fetchone()
    connection.close()

    return row_to_safe_agent(agent)


def get_available_agent_count():
    create_agent_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM support_agents
        WHERE is_active = 1
        AND is_available = 1
    """)

    count = cursor.fetchone()[0]
    connection.close()

    return int(count or 0)


def has_available_agent():
    return get_available_agent_count() > 0
