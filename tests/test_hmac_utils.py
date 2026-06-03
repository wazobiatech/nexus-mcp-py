"""Contract vector tests for HMAC signing.

These tests exercise the **production** ``sign_request`` function against
vectors.json from nexus-mcp-contract. A private reimplementation is NOT used
so that any drift in the real signer is caught here.
"""

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


@pytest.mark.parametrize("vector", VECTORS, ids=lambda v: v["id"])
def test_contract_vector(vector):
    """Production sign_request must match every contract vector."""
    expected = vector["expected"]["x-signature"]
    # Use the real sign_request with the fixed timestamp from the vector.
    got, _ = sign_request(
        vector["input"]["method"],
        vector["input"]["path"],
        vector["input"]["secret"],
        _timestamp=vector["input"]["timestamp"],
    )
    assert got == expected, f"{vector['id']} — {vector['description']}"
