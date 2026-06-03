"""Unit tests for HMACMiddleware."""

import hmac
import hashlib
import time

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from nexus_mcp.middleware import HMACMiddleware

SECRET = "test-secret"


def _sign(method: str, path: str, timestamp: str) -> str:
    payload = (method.upper() + path + timestamp).encode("utf-8")
    return hmac.new(SECRET.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _make_app():
    app = Starlette()

    @app.route("/", methods=["GET", "POST"])
    async def homepage(request: Request):
        return PlainTextResponse("ok")

    # Wrap with HMAC middleware
    wrapped = HMACMiddleware(app, SECRET)
    return wrapped


def test_valid_request():
    ts = str(int(time.time()))
    client = TestClient(_make_app())
    response = client.get(
        "/",
        headers={"x-signature": _sign("GET", "/", ts), "x-timestamp": ts},
    )
    assert response.status_code == 200
    assert response.text == "ok"


def test_missing_headers():
    client = TestClient(_make_app())
    response = client.get("/")
    assert response.status_code == 401
    assert response.json()["reason"] == "missing headers"


def test_bad_signature():
    ts = str(int(time.time()))
    client = TestClient(_make_app())
    response = client.get(
        "/",
        headers={"x-signature": "badsig", "x-timestamp": ts},
    )
    assert response.status_code == 401
    assert response.json()["reason"] == "signature mismatch"


def test_stale_timestamp():
    ts = "0"
    client = TestClient(_make_app())
    response = client.get(
        "/",
        headers={"x-signature": _sign("GET", "/", ts), "x-timestamp": ts},
    )
    assert response.status_code == 401
    assert response.json()["reason"] == "stale timestamp"
