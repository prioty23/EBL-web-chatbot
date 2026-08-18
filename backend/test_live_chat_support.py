"""Regression checks for the Human Support queue foundation.

Run from the project root:
    python backend/test_live_chat_support.py
"""

from __future__ import annotations

import sqlite3
import sys
import uuid
import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import HTTPException


BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import main  # noqa: E402
from agent_database import DEFAULT_AGENT_ID, seed_default_agent, update_agent_availability  # noqa: E402
from database import DATABASE_NAME  # noqa: E402
from live_chat_database import create_live_chat_database  # noqa: E402
from live_chat_database import (  # noqa: E402
    LIVE_CHAT_INACTIVITY_END_MESSAGE,
    LIVE_CHAT_INACTIVITY_WARNING_MESSAGE,
)
from schemas import (  # noqa: E402
    LiveChatAcceptRequest,
    LiveChatEndRequest,
    LiveChatFeedbackRequest,
    LiveChatMessageRequest,
    LiveChatStartRequest,
    LiveChatTypingRequest,
)


def cleanup_live_chat(chat_session_id: str, support_session_id: str = ""):
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    support_ids = []

    if support_session_id:
        support_ids.append(support_session_id)

    cursor.execute(
        """
        SELECT support_session_id
        FROM live_chat_sessions
        WHERE chat_session_id = ?
        """,
        (chat_session_id,),
    )
    support_ids.extend(row[0] for row in cursor.fetchall())

    for current_support_id in set(support_ids):
        cursor.execute(
            "DELETE FROM live_chat_messages WHERE support_session_id = ?",
            (current_support_id,),
        )
        cursor.execute(
            "DELETE FROM live_chat_sessions WHERE support_session_id = ?",
            (current_support_id,),
        )

    connection.commit()
    connection.close()


def assert_true(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def run_live_chat_foundation_test():
    create_live_chat_database()
    seed_default_agent()
    update_agent_availability(DEFAULT_AGENT_ID, True)
    os.environ["LIVE_CHAT_INACTIVITY_WARNING_SECONDS"] = "1"
    os.environ["LIVE_CHAT_INACTIVITY_TIMEOUT_SECONDS"] = "60"

    chat_session_id = f"live-chat-test-{uuid.uuid4().hex}"
    support_session_id = ""

    try:
        start_response = main.start_live_chat_session(
            LiveChatStartRequest(
                session_id=chat_session_id,
                customer_name="Test Customer",
                customer_phone="01700000000",
            ),
        )
        session = start_response["session"]
        support_session_id = session["support_session_id"]

        assert_true(
            start_response["message"]
            == "An EBL Support Agent will join the chat as soon as possible.",
            "Queue response message is not customer friendly.",
        )
        assert_true(session["chat_session_id"] == chat_session_id, "Chat session ID was not saved.")
        assert_true(session["customer_name"] == "Test Customer", "Customer name was not saved.")
        assert_true(session["customer_phone"] == "01700000000", "Customer phone was not saved.")
        assert_true(session["status"] == "waiting", "New live chat session is not waiting.")
        assert_true(bool(session["created_at"]), "created_at was not saved.")

        duplicate_response = main.start_live_chat_session(
            LiveChatStartRequest(
                session_id=chat_session_id,
                customer_name="Test Customer",
                customer_phone="+8801700000000",
            ),
        )
        assert_true(
            duplicate_response["session"]["support_session_id"] == support_session_id,
            "Duplicate open support request created a new session.",
        )
        assert_true(
            duplicate_response["session"].get("is_existing") is True,
            "Duplicate open support request was not marked existing.",
        )

        try:
            main.start_live_chat_session(
                LiveChatStartRequest(
                    session_id=f"invalid-live-chat-test-{uuid.uuid4().hex}",
                    customer_name="Invalid Customer",
                    customer_phone="1234567890",
                ),
            )
        except HTTPException as error:
            assert_true(error.status_code == 400, "Invalid phone should return 400.")
        else:
            raise AssertionError("Invalid phone number was accepted.")

        waiting_response = main.list_waiting_live_chat_sessions(limit=100)
        waiting_ids = {
            waiting_session["support_session_id"]
            for waiting_session in waiting_response["sessions"]
        }
        assert_true(
            support_session_id in waiting_ids,
            "Waiting session API did not return the new support request.",
        )

        accept_response = main.accept_live_chat_support_session(
            support_session_id,
            LiveChatAcceptRequest(agent_id="agent-1"),
        )
        assert_true(
            accept_response["session"]["status"] == "active",
            "Accepted live chat session did not become active.",
        )
        assert_true(
            accept_response["session"]["agent_id"] == "agent-1",
            "Agent ID was not saved during accept.",
        )

        active_response = main.get_active_live_chat_support_session()
        assert_true(
            active_response["session"]["support_session_id"] == support_session_id,
            "Active live chat session API did not return the accepted support request.",
        )

        typing_response = main.update_live_chat_typing_indicator(
            support_session_id,
            LiveChatTypingRequest(
                sender_type="agent",
                sender_id="agent-1",
                is_typing=True,
            ),
        )
        assert_true(
            typing_response["session"]["agent_is_typing"] is True,
            "Agent typing status was not turned on.",
        )

        stopped_typing_response = main.update_live_chat_typing_indicator(
            support_session_id,
            LiveChatTypingRequest(
                sender_type="agent",
                sender_id="agent-1",
                is_typing=False,
            ),
        )
        assert_true(
            stopped_typing_response["session"]["agent_is_typing"] is False,
            "Agent typing status was not turned off.",
        )

        customer_typing_response = main.update_live_chat_typing_indicator(
            support_session_id,
            LiveChatTypingRequest(
                sender_type="customer",
                sender_id=chat_session_id,
                is_typing=True,
            ),
        )
        assert_true(
            customer_typing_response["session"]["customer_is_typing"] is True,
            "Customer typing status was not turned on.",
        )

        customer_stopped_typing_response = main.update_live_chat_typing_indicator(
            support_session_id,
            LiveChatTypingRequest(
                sender_type="customer",
                sender_id=chat_session_id,
                is_typing=False,
            ),
        )
        assert_true(
            customer_stopped_typing_response["session"]["customer_is_typing"] is False,
            "Customer typing status was not turned off.",
        )

        message_response = main.create_live_chat_message(
            support_session_id,
            LiveChatMessageRequest(
                sender_type="customer",
                sender_id=chat_session_id,
                message="Hello support agent",
            ),
        )
        assert_true(
            message_response["chat_message"]["message"] == "Hello support agent",
            "Live chat message was not saved.",
        )

        messages_response = main.list_live_chat_messages(support_session_id)
        assert_true(
            any(
                chat_message["message"] == "Hello support agent"
                for chat_message in messages_response["messages"]
            ),
            "Live chat message API did not return the saved message.",
        )

        connection = sqlite3.connect(DATABASE_NAME)
        cursor = connection.cursor()
        warning_activity_time = (
            datetime.now() - timedelta(seconds=2)
        ).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            UPDATE live_chat_sessions
            SET last_activity_at = ?,
                inactivity_warning_sent_at = ''
            WHERE support_session_id = ?
            """,
            (warning_activity_time, support_session_id),
        )
        connection.commit()
        connection.close()

        warning_response = main.list_live_chat_messages(support_session_id)
        assert_true(
            any(
                chat_message["message"] == LIVE_CHAT_INACTIVITY_WARNING_MESSAGE
                for chat_message in warning_response["messages"]
            ),
            "Inactivity warning message was not added.",
        )

        connection = sqlite3.connect(DATABASE_NAME)
        cursor = connection.cursor()
        timeout_activity_time = (
            datetime.now() - timedelta(seconds=61)
        ).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            UPDATE live_chat_sessions
            SET last_activity_at = ?
            WHERE support_session_id = ?
            """,
            (timeout_activity_time, support_session_id),
        )
        connection.commit()
        connection.close()

        timeout_response = main.list_live_chat_messages(support_session_id)
        assert_true(
            timeout_response["session"]["status"] == "ended",
            "Inactive live chat session was not auto-ended.",
        )
        assert_true(
            any(
                chat_message["message"] == LIVE_CHAT_INACTIVITY_END_MESSAGE
                for chat_message in timeout_response["messages"]
            ),
            "Inactivity auto-end message was not added.",
        )

        end_response = main.end_live_chat_support_session(
            support_session_id,
            LiveChatEndRequest(ended_by="agent-1"),
        )
        assert_true(
            end_response["session"]["status"] == "ended",
            "Ended live chat session did not become ended.",
        )

        history_response = main.list_live_chat_history_sessions(limit=100)
        history_ids = {
            history_session["support_session_id"]
            for history_session in history_response["sessions"]
        }
        assert_true(
            support_session_id in history_ids,
            "Ended live chat session was not returned in history.",
        )

        feedback_response = main.submit_live_chat_feedback(
            support_session_id,
            LiveChatFeedbackRequest(feedback="helpful"),
        )
        assert_true(
            feedback_response["session"]["feedback"] == "helpful",
            "Live chat feedback was not saved.",
        )
        assert_true(
            bool(feedback_response["session"]["feedback_at"]),
            "Live chat feedback timestamp was not saved.",
        )

    finally:
        os.environ.pop("LIVE_CHAT_INACTIVITY_WARNING_SECONDS", None)
        os.environ.pop("LIVE_CHAT_INACTIVITY_TIMEOUT_SECONDS", None)
        cleanup_live_chat(chat_session_id, support_session_id)


def main_entry():
    try:
        run_live_chat_foundation_test()
    except Exception as error:
        print("FAIL Human Support queue foundation")
        print(f"  - {error}")
        return 1

    print("PASS Human Support queue foundation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_entry())
