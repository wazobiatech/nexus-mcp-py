"""Async HMAC-signed HTTP client for outbound Nexus service requests."""

import httpx

from nexus_mcp.hmac_utils import sign_request


class HMACClient:
    """Async HTTP client that automatically signs every request with HMAC-SHA256.

    Usage::

        async with HMACClient(base_url="http://mercury:4001", secret=settings.MERCURY_HMAC_SECRET) as client:
            response = await client.get("/mcp/manifest")
            manifest = response.json()
    """

    def __init__(self, base_url: str, secret: str, **httpx_kwargs) -> None:
        self._secret = secret
        self._client = httpx.AsyncClient(base_url=base_url, **httpx_kwargs)

    def _auth_headers(self, method: str, path: str) -> dict[str, str]:
        sig, ts = sign_request(method, path, self._secret)
        return {"x-signature": sig, "x-timestamp": ts}

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self._client.get(path, headers=self._auth_headers("GET", path), **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self._client.post(path, headers=self._auth_headers("POST", path), **kwargs)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "HMACClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.aclose()
