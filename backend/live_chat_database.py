import sqlite3
import uuid
from datetime import datetime

from database import DATABASE_NAME, add_column_if_missing, create_database


WAITING_STATUS = "waiting"
ACTIVE_STATUS = "active"
ENDED_STATUS = "ended"

CUSTOMER_SENDER = "customer"
AGENT_SENDER = "agent"
SYSTEM_SENDER = "system"


def current_time_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def row_to_dict(row):
    if not row:
        return None

    return dict(row)


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def create_live_chat_database():
    create_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS live_chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            support_session_id TEXT UNIQUE,
            chat_session_id TEXT,
            customer_name TEXT,
            customer_phone TEXT,
            status TEXT,
            agent_id TEXT,
            created_at TEXT,
            accepted_at TEXT,
            ended_at TEXT,
            feedback TEXT,
            feedback_at TEXT,
            updated_at TEXT
        )
    """)

    add_column_if_missing(
        cursor,
        "live_chat_sessions",
        "customer_phone",
        "TEXT",
    )
    add_column_if_missing(
        cursor,
        "live_chat_sessions",
        "feedback",
        "TEXT",
    )
    add_column_if_missing(
        cursor,
        "live_chat_sessions",
        "feedback_at",
        "TEXT",
    )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS live_chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            support_session_id TEXT,
            sender_type TEXT,
            sender_id TEXT,
            message TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_live_chat_sessions_status
        ON live_chat_sessions (status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_live_chat_sessions_chat_session
        ON live_chat_sessions (chat_session_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_live_chat_messages_session
        ON live_chat_messages (support_session_id, id)
    """)

    connection.commit()
    connection.close()


def generate_support_session_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"LIVE-{timestamp}-{suffix}"


def get_live_chat_session(support_session_id):
    create_live_chat_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM live_chat_sessions
        WHERE support_session_id = ?
    """, (support_session_id,))

    session = row_to_dict(cursor.fetchone())
    connection.close()

    return session


def get_existing_open_live_chat_session(chat_session_id):
    create_live_chat_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM live_chat_sessions
        WHERE chat_session_id = ?
        AND status IN (?, ?)
        ORDER BY id DESC
        LIMIT 1
    """, (
        chat_session_id,
        WAITING_STATUS,
        ACTIVE_STATUS,
    ))

    session = row_to_dict(cursor.fetchone())
    connection.close()

    return session


def create_live_chat_session(chat_session_id, customer_name="Customer", customer_phone=""):
    create_live_chat_database()

    normalized_customer_name = (customer_name or "Customer").strip() or "Customer"
    normalized_customer_phone = (customer_phone or "").strip()
    existing_session = get_existing_open_live_chat_session(chat_session_id)

    if existing_session:
        updated_customer_name = normalized_customer_name or existing_session.get("customer_name") or "Customer"
        updated_customer_phone = (
            normalized_customer_phone
            or existing_session.get("customer_phone")
            or ""
        )

        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE live_chat_sessions
            SET customer_name = ?,
                customer_phone = ?,
                updated_at = ?
            WHERE support_session_id = ?
        """, (
            updated_customer_name,
            updated_customer_phone,
            current_time_string(),
            existing_session["support_session_id"],
        ))
        connection.commit()
        connection.close()

        updated_session = get_live_chat_session(existing_session["support_session_id"])
        updated_session["is_existing"] = True
        return updated_session

    now = current_time_string()
    support_session_id = generate_support_session_id()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO live_chat_sessions (
            support_session_id,
            chat_session_id,
            customer_name,
            customer_phone,
            status,
            agent_id,
            created_at,
            accepted_at,
            ended_at,
            feedback,
            feedback_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        support_session_id,
        chat_session_id,
        normalized_customer_name,
        normalized_customer_phone,
        WAITING_STATUS,
        "",
        now,
        "",
        "",
        "",
        "",
        now,
    ))

    connection.commit()
    connection.close()

    session = get_live_chat_session(support_session_id)
    session["is_existing"] = False
    return session


def get_waiting_live_chat_sessions(limit=20):
    create_live_chat_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM live_chat_sessions
        WHERE status = ?
        ORDER BY created_at ASC, id ASC
        LIMIT ?
    """, (
        WAITING_STATUS,
        limit,
    ))

    sessions = [row_to_dict(row) for row in cursor.fetchall()]
    connection.close()

    return sessions


def get_active_live_chat_session():
    create_live_chat_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM live_chat_sessions
        WHERE status = ?
        ORDER BY accepted_at ASC, id ASC
        LIMIT 1
    """, (ACTIVE_STATUS,))

    session = row_to_dict(cursor.fetchone())
    connection.close()

    return session


def accept_live_chat_session(support_session_id, agent_id="agent"):
    create_live_chat_database()

    session = get_live_chat_session(support_session_id)

    if not session:
        return {
            "accepted": False,
            "reason": "not_found",
            "session": None,
        }

    if session["status"] == ENDED_STATUS:
        return {
            "accepted": False,
            "reason": "ended",
            "session": session,
        }

    active_session = get_active_live_chat_session()

    if active_session and active_session["support_session_id"] != support_session_id:
        return {
            "accepted": False,
            "reason": "active_chat_exists",
            "session": session,
            "active_session": active_session,
        }

    if session["status"] == ACTIVE_STATUS:
        return {
            "accepted": True,
            "reason": "already_active",
            "session": session,
        }

    now = current_time_string()
    normalized_agent_id = (agent_id or "agent").strip() or "agent"

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE live_chat_sessions
        SET status = ?,
            agent_id = ?,
            accepted_at = ?,
            updated_at = ?
        WHERE support_session_id = ?
    """, (
        ACTIVE_STATUS,
        normalized_agent_id,
        now,
        now,
        support_session_id,
    ))

    connection.commit()
    connection.close()

    return {
        "accepted": True,
        "reason": "accepted",
        "session": get_live_chat_session(support_session_id),
    }


def save_live_chat_message(support_session_id, sender_type, message, sender_id=""):
    create_live_chat_database()

    session = get_live_chat_session(support_session_id)

    if not session:
        return {
            "saved": False,
            "reason": "not_found",
            "message": None,
        }

    if session["status"] == ENDED_STATUS:
        return {
            "saved": False,
            "reason": "ended",
            "message": None,
        }

    normalized_sender_type = (sender_type or "").strip().lower()

    if normalized_sender_type not in [CUSTOMER_SENDER, AGENT_SENDER, SYSTEM_SENDER]:
        return {
            "saved": False,
            "reason": "invalid_sender_type",
            "message": None,
        }

    normalized_message = (message or "").strip()

    if not normalized_message:
        return {
            "saved": False,
            "reason": "empty_message",
            "message": None,
        }

    now = current_time_string()
    normalized_sender_id = (sender_id or "").strip()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO live_chat_messages (
            support_session_id,
            sender_type,
            sender_id,
            message,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        support_session_id,
        normalized_sender_type,
        normalized_sender_id,
        normalized_message,
        now,
    ))

    message_id = cursor.lastrowid

    cursor.execute("""
        UPDATE live_chat_sessions
        SET updated_at = ?
        WHERE support_session_id = ?
    """, (
        now,
        support_session_id,
    ))

    connection.commit()

    cursor.execute("""
        SELECT *
        FROM live_chat_messages
        WHERE id = ?
    """, (message_id,))

    saved_message = row_to_dict(cursor.fetchone())
    connection.close()

    return {
        "saved": True,
        "reason": "saved",
        "message": saved_message,
    }


def get_live_chat_messages(support_session_id, after_id=0, limit=100):
    create_live_chat_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM live_chat_messages
        WHERE support_session_id = ?
        AND id > ?
        ORDER BY id ASC
        LIMIT ?
    """, (
        support_session_id,
        after_id,
        limit,
    ))

    messages = [row_to_dict(row) for row in cursor.fetchall()]
    connection.close()

    return messages


def save_live_chat_feedback(support_session_id, feedback):
    create_live_chat_database()

    session = get_live_chat_session(support_session_id)

    if not session:
        return {
            "saved": False,
            "reason": "not_found",
            "session": None,
        }

    normalized_feedback = (feedback or "").strip().lower()

    if normalized_feedback not in ["helpful", "not_helpful"]:
        return {
            "saved": False,
            "reason": "invalid_feedback",
            "session": session,
        }

    now = current_time_string()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE live_chat_sessions
        SET feedback = ?,
            feedback_at = ?,
            updated_at = ?
        WHERE support_session_id = ?
    """, (
        normalized_feedback,
        now,
        now,
        support_session_id,
    ))

    connection.commit()
    connection.close()

    return {
        "saved": True,
        "reason": "saved",
        "session": get_live_chat_session(support_session_id),
    }


def end_live_chat_session(support_session_id, ended_by="agent"):
    create_live_chat_database()

    session = get_live_chat_session(support_session_id)

    if not session:
        return {
            "ended": False,
            "reason": "not_found",
            "session": None,
        }

    if session["status"] == ENDED_STATUS:
        return {
            "ended": True,
            "reason": "already_ended",
            "session": session,
        }

    ended_by_label = (ended_by or "agent").strip() or "agent"
    save_live_chat_message(
        support_session_id=support_session_id,
        sender_type=SYSTEM_SENDER,
        sender_id="system",
        message=f"Live chat session ended by {ended_by_label}.",
    )

    now = current_time_string()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE live_chat_sessions
        SET status = ?,
            ended_at = ?,
            updated_at = ?
        WHERE support_session_id = ?
    """, (
        ENDED_STATUS,
        now,
        now,
        support_session_id,
    ))

    connection.commit()
    connection.close()

    return {
        "ended": True,
        "reason": "ended",
        "session": get_live_chat_session(support_session_id),
    }
