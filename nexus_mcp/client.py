"""Async HMAC-signed HTTP client for outbound Nexus service requests."""

import httpx

from nexus_mcp.hmac_utils import sign_request


class HMACClient:
    """Async HTTP client that automatically signs every request with HMAC-SHA256.

    The HMAC signature covers the full path **including query string**, so
    ``params=`` kwargs are resolved into the path before signing. This matches
    the server-side middleware which signs ``request.url.path + "?" + request.url.query``.

    Usage::

        async with HMACClient(
            base_url="http://mercury:4001",
            secret=settings.MERCURY_HMAC_SECRET,
        ) as client:
            response = await client.get("/mcp/manifest")
            manifest = response.json()
    """

    def __init__(self, base_url: str, secret: str, **httpx_kwargs) -> None:
        """Initialise the client.

        Args:
            base_url: Base URL for all requests (e.g. ``http://mercury:4001``).
            secret: Shared HMAC-SHA256 secret.
            **httpx_kwargs: Forwarded to ``httpx.AsyncClient``.
        """
        self._secret = secret
        self._client = httpx.AsyncClient(base_url=base_url, **httpx_kwargs)

    def _auth_headers(self, method: str, path: str) -> dict[str, str]:
        """Return ``x-signature`` and ``x-timestamp`` headers for *path*.

        Args:
            method: HTTP method (``GET``, ``POST``, …).
            path: Full path **including** query string, no fragment, no host.

        Returns:
            Dict with ``x-signature`` and ``x-timestamp`` keys.
        """
        sig, ts = sign_request(method, path, self._secret)
        return {"x-signature": sig, "x-timestamp": ts}

    def _signed_path(self, path: str, params: dict | None) -> str:
        """Return the full path with query string, suitable for signing.

        httpx encodes ``params=`` into the URL after this call, so we must
        do the same encoding here to keep the signature in sync.

        Args:
            path: Raw path string (e.g. ``/mcp/manifest``).
            params: Optional query parameters dict.

        Returns:
            Path with query string appended if *params* is non-empty.
        """
        if not params:
            return path
        encoded = httpx.QueryParams(params)
        return f"{path}?{encoded}"

    async def get(self, path: str, **kwargs) -> httpx.Response:
        """Send a signed GET request.

        Args:
            path: Request path. Query params may be passed via ``params=``.
            **kwargs: Forwarded to ``httpx.AsyncClient.get``.

        Returns:
            The HTTP response.
        """
        signed_path = self._signed_path(path, kwargs.get("params"))
        headers = {**kwargs.pop("headers", {}), **self._auth_headers("GET", signed_path)}
        return await self._client.get(path, headers=headers, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        """Send a signed POST request.

        HMAC headers take precedence over caller-supplied headers so they
        cannot be spoofed.

        Args:
            path: Request path.
            **kwargs: Forwarded to ``httpx.AsyncClient.post``.

        Returns:
            The HTTP response.
        """
        signed_path = self._signed_path(path, kwargs.get("params"))
        headers = {**kwargs.pop("headers", {}), **self._auth_headers("POST", signed_path)}
        return await self._client.post(path, headers=headers, **kwargs)

    async def aclose(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()

    async def __aenter__(self) -> "HMACClient":
        """Enter async context manager."""
        return self

    async def __aexit__(self, *args) -> None:
        """Exit async context manager and close the client."""
        await self.aclose()
