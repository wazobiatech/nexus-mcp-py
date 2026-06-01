"""MCP server factory for FastAPI."""

from typing import Any

from fastapi import FastAPI, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from nexus_mcp.middleware import HMACMiddleware
from nexus_mcp.models import Manifest, MCPToolDefinition


def create_mcp_server(
    port: int,
    hmac_secret: str,
    manifest: Manifest,
    tools: list[MCPToolDefinition],
) -> FastAPI:
    """Create a FastAPI application with HMAC protection and MCP endpoints.

    Args:
        port: Port number (logged at startup, not bound here).
        hmac_secret: Shared symmetric key for HMAC verification.
        manifest: Service manifest.
        tools: List of tool definitions.

    Returns:
        Configured FastAPI application. Start with uvicorn::

            uvicorn.run(app, host="0.0.0.0", port=port)
    """
    app = FastAPI(title="Nexus MCP Server", version=manifest.version)

    # HMAC middleware
    app.add_middleware(BaseHTTPMiddleware, dispatch=HMACMiddleware(app, hmac_secret).dispatch)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/mcp/manifest")
    async def get_manifest() -> Manifest:
        return manifest

    @app.post("/mcp/call")
    async def call_tool(body: dict[str, Any]) -> dict[str, Any]:
        tool_name = body.get("tool")
        arguments = body.get("arguments", {})

        tool = next((t for t in tools if t.name == tool_name), None)
        if tool is None:
            raise HTTPException(status_code=404, detail=f"tool not found: {tool_name}")

        # NOTE: In a real implementation, tools would have callable handlers.
        # This SDK layer returns a placeholder; services inject their own handlers.
        return {"result": {"tool": tool_name, "arguments": arguments}}

    return app
