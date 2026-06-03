"""FastAPI/Starlette HMAC middleware."""

import hashlib
import hmac
import time
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_MAX_AGE_SECONDS = 300
_HEADER_SIGNATURE = "x-signature"
_HEADER_TIMESTAMP = "x-timestamp"


def _compute_signature(method: str, path: str, timestamp: str, secret: str) -> str:
    payload = (method.upper() + path + timestamp).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


class HMACMiddleware(BaseHTTPMiddleware):
    """Validate HMAC-SHA256 signatures on incoming requests."""

    def __init__(self, app: Callable[[Request], Awaitable], hmac_secret: str) -> None:
        super().__init__(app)
        self.hmac_secret = hmac_secret

    # Paths exempt from HMAC — kubelet probes don't send signed requests
    _UNPROTECTED = {"/health", "/health/live", "/health/ready"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self._UNPROTECTED:
            return await call_next(request)

        sig = request.headers.get(_HEADER_SIGNATURE)
        ts = request.headers.get(_HEADER_TIMESTAMP)

        if not sig or not ts:
            return JSONResponse(
                {"error": "unauthorized", "reason": "missing headers"},
                status_code=401,
            )

        try:
            timestamp = int(ts)
        except ValueError:
            return JSONResponse(
                {"error": "unauthorized", "reason": "invalid timestamp"},
                status_code=401,
            )

        now = int(time.time())
        if abs(now - timestamp) > _MAX_AGE_SECONDS:
            return JSONResponse(
                {"error": "unauthorized", "reason": "stale timestamp"},
                status_code=401,
            )

        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query}"
        expected = _compute_signature(request.method, path, ts, self.hmac_secret)
        if not hmac.compare_digest(expected, sig):
            return JSONResponse(
                {"error": "unauthorized", "reason": "signature mismatch"},
                status_code=401,
            )

        return await call_next(request)
