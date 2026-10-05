"""Unit tests for BGG login diagnostics (no network access)."""

from unittest.mock import MagicMock, patch

import pytest
from loguru import logger

from my_board_games.bgg_api import BGGClient


@pytest.fixture
def log_messages():
    messages = []
    handler_id = logger.add(lambda m: messages.append(m.record["message"]), level="INFO")
    yield messages
    logger.remove(handler_id)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("BGG_USERNAME", "someone")
    monkeypatch.setenv("BGG_PASSWORD", "secret")
    # Skip the real login during construction; tests call it explicitly
    with patch.object(BGGClient, "_login_for_private_info"):
        return BGGClient()


def _response(status, text="", headers=None):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    resp.headers = headers or {}
    return resp


def test_login_failure_logs_cloudflare_header_and_body(client, log_messages):
    html = "<!DOCTYPE html>\n<html><head><title>Just a moment...</title></head></html>"
    client.session.post = MagicMock(
        return_value=_response(403, html, {"cf-mitigated": "challenge"})
    )

    assert client._login_for_private_info() is False

    failure = [m for m in log_messages if "login failed" in m]
    assert len(failure) == 1
    assert "403" in failure[0]
    assert "cf-mitigated=challenge" in failure[0]
    assert "Just a moment..." in failure[0]
    assert "\n" not in failure[0]


def test_login_failure_logs_bgg_json_error(client, log_messages):
    body = '{"errors":{"message":"Invalid username or password"}}'
    client.session.post = MagicMock(return_value=_response(400, body))

    assert client._login_for_private_info() is False

    failure = [m for m in log_messages if "login failed" in m]
    assert len(failure) == 1
    assert "400" in failure[0]
    assert "cf-mitigated=None" in failure[0]
    assert "Invalid username or password" in failure[0]


def test_login_failure_truncates_long_body(client, log_messages):
    client.session.post = MagicMock(return_value=_response(403, "x" * 5000))

    client._login_for_private_info()

    failure = [m for m in log_messages if "login failed" in m]
    assert "x" * 200 in failure[0]
    assert "x" * 201 not in failure[0]


def test_login_failure_does_not_log_password(client, log_messages):
    client.session.post = MagicMock(return_value=_response(403, "denied"))

    client._login_for_private_info()

    assert not any("secret" in m for m in log_messages)
