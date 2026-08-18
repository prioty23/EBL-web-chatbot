import sqlite3
import uuid
from datetime import datetime, timedelta
import os

from database import DATABASE_NAME, add_column_if_missing, create_database


WAITING_STATUS = "waiting"
ACTIVE_STATUS = "active"
ENDED_STATUS = "ended"

CUSTOMER_SENDER = "customer"
AGENT_SENDER = "agent"
SYSTEM_SENDER = "system"

LIVE_CHAT_INACTIVITY_WARNING_MESSAGE = (
    "This live chat session will end soon due to inactivity. "
    "Please send a message if you still need support."
)
LIVE_CHAT_INACTIVITY_END_MESSAGE = "Live chat session ended due to inactivity."
DEFAULT_INACTIVITY_WARNING_SECONDS = 180
DEFAULT_INACTIVITY_TIMEOUT_SECONDS = 300


def current_time_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_time_string(value):
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def future_time_string(seconds):
    return (datetime.now() + timedelta(seconds=seconds)).strftime("%Y-%m-%d %H:%M:%S")


def is_future_time(value):
    if not value:
        return False

    try:
        parsed_time = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False

    return parsed_time > datetime.now()


def get_timeout_seconds(env_name, default_value):
    try:
        value = int(os.getenv(env_name, str(default_value)))
    except ValueError:
        return default_value

    return max(1, value)


def row_to_dict(row):
    if not row:
        return None

    data = dict(row)
    data["agent_is_typing"] = is_future_time(data.get("agent_typing_until", ""))
    data["customer_is_typing"] = is_future_time(data.get("customer_typing_until", ""))
    return data


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
            agent_typing_until TEXT,
            customer_typing_until TEXT,
            last_activity_at TEXT,
            inactivity_warning_sent_at TEXT,
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
    add_column_if_missing(
        cursor,
        "live_chat_sessions",
        "agent_typing_until",
        "TEXT",
    )
    add_column_if_missing(
        cursor,
        "live_chat_sessions",
        "customer_typing_until",
        "TEXT",
    )
    add_column_if_missing(
        cursor,
        "live_chat_sessions",
        "last_activity_at",
        "TEXT",
    )
    add_column_if_missing(
        cursor,
        "live_chat_sessions",
        "inactivity_warning_sent_at",
        "TEXT",
    )

    now = current_time_string()
    cursor.execute("""
        UPDATE live_chat_sessions
        SET last_activity_at = COALESCE(NULLIF(updated_at, ''), NULLIF(created_at, ''), ?)
        WHERE last_activity_at IS NULL
        OR last_activity_at = ''
    """, (now,))

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
            agent_typing_until,
            customer_typing_until,
            last_activity_at,
            inactivity_warning_sent_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        "",
        "",
        now,
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


def get_live_chat_history_sessions(limit=20):
    create_live_chat_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM live_chat_sessions
        WHERE status = ?
        ORDER BY ended_at DESC, updated_at DESC, id DESC
        LIMIT ?
    """, (
        ENDED_STATUS,
        limit,
    ))

    sessions = [row_to_dict(row) for row in cursor.fetchall()]
    connection.close()

    return sessions


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
            last_activity_at = ?,
            inactivity_warning_sent_at = ?,
            updated_at = ?
        WHERE support_session_id = ?
    """, (
        ACTIVE_STATUS,
        normalized_agent_id,
        now,
        now,
        "",
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

    if normalized_sender_type == AGENT_SENDER:
        cursor.execute("""
            UPDATE live_chat_sessions
            SET agent_typing_until = ?,
                last_activity_at = ?,
                inactivity_warning_sent_at = ?,
                updated_at = ?
            WHERE support_session_id = ?
        """, (
            "",
            now,
            "",
            now,
            support_session_id,
        ))
    elif normalized_sender_type == CUSTOMER_SENDER:
        cursor.execute("""
            UPDATE live_chat_sessions
            SET customer_typing_until = ?,
                last_activity_at = ?,
                inactivity_warning_sent_at = ?,
                updated_at = ?
            WHERE support_session_id = ?
        """, (
            "",
            now,
            "",
            now,
            support_session_id,
        ))
    else:
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


def update_live_chat_typing_status(
    support_session_id,
    sender_type,
    sender_id="",
    is_typing=False,
    seconds=4,
):
    create_live_chat_database()

    session = get_live_chat_session(support_session_id)

    if not session:
        return {
            "updated": False,
            "reason": "not_found",
            "session": None,
        }

    if session["status"] == ENDED_STATUS:
        return {
            "updated": False,
            "reason": "ended",
            "session": session,
        }

    normalized_sender_type = (sender_type or "").strip().lower()

    if normalized_sender_type not in [AGENT_SENDER, CUSTOMER_SENDER]:
        return {
            "updated": False,
            "reason": "invalid_sender_type",
            "session": session,
        }

    if normalized_sender_type == AGENT_SENDER and session["status"] != ACTIVE_STATUS:
        return {
            "updated": False,
            "reason": "not_active",
            "session": session,
        }

    if normalized_sender_type == CUSTOMER_SENDER and session["status"] not in [WAITING_STATUS, ACTIVE_STATUS]:
        return {
            "updated": False,
            "reason": "not_active",
            "session": session,
        }

    normalized_sender_id = (sender_id or "").strip()

    if (
        normalized_sender_type == AGENT_SENDER
        and session.get("agent_id")
        and normalized_sender_id
        and session["agent_id"] != normalized_sender_id
    ):
        return {
            "updated": False,
            "reason": "wrong_agent",
            "session": session,
        }

    if (
        normalized_sender_type == CUSTOMER_SENDER
        and session.get("chat_session_id")
        and normalized_sender_id
        and session["chat_session_id"] != normalized_sender_id
    ):
        return {
            "updated": False,
            "reason": "wrong_customer",
            "session": session,
        }

    now = current_time_string()
    typing_until = future_time_string(seconds) if is_typing else ""
    typing_column = (
        "agent_typing_until"
        if normalized_sender_type == AGENT_SENDER
        else "customer_typing_until"
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(f"""
        UPDATE live_chat_sessions
        SET {typing_column} = ?,
            last_activity_at = ?,
            inactivity_warning_sent_at = ?,
            updated_at = ?
        WHERE support_session_id = ?
    """, (
        typing_until,
        now,
        "",
        now,
        support_session_id,
    ))

    connection.commit()
    connection.close()

    return {
        "updated": True,
        "reason": "updated",
        "session": get_live_chat_session(support_session_id),
    }


def refresh_live_chat_session_timeout(support_session_id):
    create_live_chat_database()

    session = get_live_chat_session(support_session_id)

    if not session or session["status"] != ACTIVE_STATUS:
        return session

    warning_seconds = get_timeout_seconds(
        "LIVE_CHAT_INACTIVITY_WARNING_SECONDS",
        DEFAULT_INACTIVITY_WARNING_SECONDS,
    )
    timeout_seconds = get_timeout_seconds(
        "LIVE_CHAT_INACTIVITY_TIMEOUT_SECONDS",
        DEFAULT_INACTIVITY_TIMEOUT_SECONDS,
    )

    if warning_seconds >= timeout_seconds:
        warning_seconds = max(1, timeout_seconds - 60)

    last_activity = parse_time_string(
        session.get("last_activity_at")
        or session.get("updated_at")
        or session.get("created_at")
    )

    if not last_activity:
        return session

    inactive_seconds = (datetime.now() - last_activity).total_seconds()

    if inactive_seconds >= timeout_seconds:
        result = end_live_chat_session(
            support_session_id=support_session_id,
            ended_by="inactivity",
        )
        return result["session"]

    if inactive_seconds < warning_seconds or session.get("inactivity_warning_sent_at"):
        return session

    save_live_chat_message(
        support_session_id=support_session_id,
        sender_type=SYSTEM_SENDER,
        sender_id="system",
        message=LIVE_CHAT_INACTIVITY_WARNING_MESSAGE,
    )

    now = current_time_string()
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE live_chat_sessions
        SET inactivity_warning_sent_at = ?,
            updated_at = ?
        WHERE support_session_id = ?
    """, (
        now,
        now,
        support_session_id,
    ))
    connection.commit()
    connection.close()

    return get_live_chat_session(support_session_id)


def refresh_live_chat_timeouts():
    create_live_chat_database()

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT support_session_id
        FROM live_chat_sessions
        WHERE status = ?
    """, (ACTIVE_STATUS,))

    support_session_ids = [row["support_session_id"] for row in cursor.fetchall()]
    connection.close()

    for support_session_id in support_session_ids:
        refresh_live_chat_session_timeout(support_session_id)


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
    system_message = (
        LIVE_CHAT_INACTIVITY_END_MESSAGE
        if ended_by_label.lower() == "inactivity"
        else f"Live chat session ended by {ended_by_label}."
    )
    save_live_chat_message(
        support_session_id=support_session_id,
        sender_type=SYSTEM_SENDER,
        sender_id="system",
        message=system_message,
    )

    now = current_time_string()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE live_chat_sessions
        SET status = ?,
            ended_at = ?,
            agent_typing_until = ?,
            customer_typing_until = ?,
            inactivity_warning_sent_at = ?,
            updated_at = ?
        WHERE support_session_id = ?
    """, (
        ENDED_STATUS,
        now,
        "",
        "",
        "",
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
