"""HMAC-SHA256 signing utilities for Nexus MCP."""

import hmac
import hashlib
import time


def sign_request(method: str, path: str, secret: str) -> tuple[str, str]:
    """Sign an HTTP request using the Nexus MCP HMAC-SHA256 algorithm.

    Payload construction (UTF-8 bytes)::

        payload = METHOD.upper().encode('utf-8') + path.encode('utf-8') + timestamp.encode('utf-8')

    Where ``timestamp`` is ``str(int(time.time()))`` (UTC Unix seconds).

    Digest computation::

        digest = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()

    Args:
        method: HTTP method (e.g. ``GET``, ``POST``).
        path: Full request path including query string. No fragment, no host.
        secret: Shared symmetric key.

    Returns:
        A tuple of ``(x_signature, x_timestamp)`` where both values are strings.
    """
    timestamp = str(int(time.time()))
    payload = (method.upper() + path + timestamp).encode("utf-8")
    key = secret.encode("utf-8")
    digest = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return digest, timestamp
