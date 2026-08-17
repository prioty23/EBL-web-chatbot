"""Regression checks for EBL support agent login.

Run from the project root:
    python backend/test_agent_login.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import HTTPException


BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import main  # noqa: E402
from agent_database import DEFAULT_AGENT_EMAIL, DEFAULT_AGENT_PASSWORD, seed_default_agent  # noqa: E402
from schemas import AgentLoginRequest  # noqa: E402


def assert_true(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def run_agent_login_test():
    seed_default_agent()

    response = main.login_support_agent(
        AgentLoginRequest(
            email=DEFAULT_AGENT_EMAIL,
            password=DEFAULT_AGENT_PASSWORD,
        ),
    )

    agent = response["agent"]

    assert_true(response["message"] == "Agent login successful.", "Login response message changed.")
    assert_true(agent["agent_id"] == "ebl-support-agent", "Default support agent ID is incorrect.")
    assert_true(agent["email"] == DEFAULT_AGENT_EMAIL, "Default support agent email is incorrect.")
    assert_true("password_hash" not in agent, "Password hash must not be returned.")
    assert_true("password_salt" not in agent, "Password salt must not be returned.")

    try:
        main.login_support_agent(
            AgentLoginRequest(
                email=DEFAULT_AGENT_EMAIL,
                password="wrong-password",
            ),
        )
    except HTTPException as error:
        assert_true(error.status_code == 401, "Wrong password should return 401.")
    else:
        raise AssertionError("Wrong password was accepted.")


def main_entry():
    try:
        run_agent_login_test()
    except Exception as error:
        print("FAIL Support agent login")
        print(f"  - {error}")
        return 1

    print("PASS Support agent login")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_entry())
