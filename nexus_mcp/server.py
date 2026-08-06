"""MCP server factory for FastAPI."""

from typing import Any, Union

from fastapi import FastAPI, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from nexus_mcp.middleware import HMACMiddleware
from nexus_mcp.models import CATALOG_FIELD_ORDER, MCPToolDefinition, Manifest


def create_mcp_server(
    port: int,
    hmac_secret: str,
    manifest: Union[Manifest, dict[str, Any]],
    tools: list[MCPToolDefinition],
) -> FastAPI:
    """Create a FastAPI application with HMAC protection and MCP endpoints.

    Args:
        port: Port number (logged at startup, not bound here).
        hmac_secret: Shared symmetric key for HMAC verification.
        manifest: Service manifest — either the typed `Manifest` Pydantic
            model or a pre-built dict (use the dict form when carrying
            service-specific extra fields that the SDK doesn't know
            about, or when assembling the manifest from multiple
            sources).
        tools: List of tool definitions.

    Returns:
        Configured FastAPI application. Start with uvicorn::

            uvicorn.run(app, host="0.0.0.0", port=port)
    """
    # Resolve the version label for the FastAPI app metadata. Falls back
    # to "0.0.0" for dict-shaped manifests that omit it (defensive — every
    # real service sets it).
    if isinstance(manifest, Manifest):
        app_version = manifest.version
        manifest_payload: dict[str, Any] = manifest.model_dump_canonical(mode="json")
    else:
        app_version = str(manifest.get("version", "0.0.0"))
        manifest_payload = _canonicalise_manifest_dict(manifest)

    app = FastAPI(title="Nexus MCP Server", version=app_version)

    # HMAC middleware
    app.add_middleware(BaseHTTPMiddleware, dispatch=HMACMiddleware(app, hmac_secret).dispatch)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/mcp/manifest")
    async def get_manifest() -> dict[str, Any]:
        """Return the service manifest including catalog fields.

        The catalog fields (does_not_own, emits, consumes, graphql_queries,
        graphql_mutations, known_gaps, auth_planes, dependencies,
        rest_endpoints) come from the typed `Manifest` model's extras, or
        from the dict passed by the caller. Empty fields are omitted to
        keep the wire payload tight.
        """
        return manifest_payload

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


def _canonicalise_manifest_dict(manifest: dict[str, Any]) -> dict[str, Any]:
    """Reorder a dict-shaped manifest into mercury's canonical key order.

    Drop empty catalog fields so the wire payload stays compact. Any
    keys not in the canonical list are kept at the end in their original
    order (e.g. prometheus's `service`/`protocol`/`mcp_endpoint`).
    """
    out: dict[str, Any] = {}

    # 1. Typed base fields first.
    for key in ("name", "namespace", "version", "description", "context"):
        if key in manifest:
            out[key] = manifest[key]

    # 2. Catalog fields in canonical order — only when non-empty.
    for key in CATALOG_FIELD_ORDER:
        value = manifest.get(key)
        if value:  # skip empty lists / dicts
            out[key] = value

    # 3. tools.
    if "tools" in manifest:
        out["tools"] = manifest["tools"]

    # 4. Service-specific extras at the end. Skip empty catalog fields
    #    (they were already dropped in step 2; don't re-introduce them
    #    here just because they happened to be empty).
    for key, value in manifest.items():
        if key in out:
            continue
        if key in CATALOG_FIELD_ORDER and not value:
            continue
        out[key] = value

    return out
