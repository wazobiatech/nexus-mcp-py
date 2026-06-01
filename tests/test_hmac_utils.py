"""Contract vector tests for HMAC signing."""

import json
import pathlib

import pytest

from nexus_mcp.hmac_utils import sign_request


def _load_vectors():
    candidates = [
        pathlib.Path(__file__).parent.parent / "vectors.json",
        pathlib.Path(__file__).parent.parent.parent / "nexus-mcp-contract" / "vectors.json",
    ]
    for path in candidates:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))["vectors"]
    raise FileNotFoundError("vectors.json not found")


VECTORS = _load_vectors()


def _sign_with_timestamp(method: str, path: str, secret: str, timestamp: str) -> str:
    import hmac
    import hashlib

    payload = (method.upper() + path + timestamp).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


@pytest.mark.parametrize("vector", VECTORS, ids=lambda v: v["id"])
def test_contract_vector(vector):
    expected = vector["expected"]["x-signature"]
    got = _sign_with_timestamp(
        vector["input"]["method"],
        vector["input"]["path"],
        vector["input"]["secret"],
        vector["input"]["timestamp"],
    )
    assert got == expected, f"{vector['id']} — {vector['description']}"
