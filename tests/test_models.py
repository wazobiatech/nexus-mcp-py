"""Smoke tests for the Manifest model — canonical key order, optional
catalog fields, extra=allow, and dict-input compatibility with create_mcp_server.
"""

from __future__ import annotations

from typing import Any

import pytest

from nexus_mcp.models import (
    CATALOG_FIELD_ORDER,
    Manifest,
    ManifestContext,
    MCPToolDefinition,
)
from nexus_mcp.server import _canonicalise_manifest_dict, create_mcp_server


def _make_manifest(**catalog: Any) -> Manifest:
    """Construct a Manifest with optional catalog field overrides."""
    return Manifest(
        name="thoth",
        namespace="thoth",
        version="2.0.0",
        description="Thoth is the AI Knowledge Service for the Nexus platform.",
        context=ManifestContext(
            domain="Vector Embeddings",
            purpose="Embed content for similarity search.",
            bounded_context="Thoth owns the embedding lifecycle.",
            key_entities=["Workspace"],
            aggregates=["Workspace"],
        ),
        tools=[
            MCPToolDefinition(
                name="thoth__health_check",
                description="Lightweight liveness check that returns the current status of the listener.",
                inputSchema={"type": "object", "properties": {}, "required": []},
            )
        ],
        **catalog,
    )


def test_manifest_accepts_optional_catalog_fields():
    m = _make_manifest(
        does_not_own=["user authentication or identity (handled by Mercury)"],
        emits=["content.processing-events"],
        consumes=[],
        graphql_queries=["jobStatus", "serviceInfo"],
        graphql_mutations=["createWorkspace"],
        known_gaps=["src/...:42 — refactor TODO"],
        auth_planes=["project-token", "hmac"],
        dependencies=["mercury"],
        rest_endpoints=[{"method": "GET", "path": "/health", "auth": "none"}],
    )
    dumped = m.model_dump_canonical(mode="json")
    assert dumped["does_not_own"] == ["user authentication or identity (handled by Mercury)"]
    assert dumped["emits"] == ["content.processing-events"]
    assert dumped["graphql_queries"] == ["jobStatus", "serviceInfo"]


def test_manifest_canonical_key_order_matches_mercury():
    m = _make_manifest(
        does_not_own=["x"],
        emits=["topic.a"],
        consumes=["topic.consumer"],  # non-empty so it stays in the wire payload
        graphql_queries=["q1"],
        graphql_mutations=["m1"],
        known_gaps=["g1"],
        auth_planes=["hmac"],
        dependencies=["mercury"],
        rest_endpoints=[{"method": "GET", "path": "/x", "auth": "none"}],
    )
    dumped = m.model_dump_canonical(mode="json")
    keys = list(dumped.keys())

    # Base + catalog fields in canonical order, then tools last.
    expected_prefix = (
        "name",
        "namespace",
        "version",
        "description",
        "context",
        "does_not_own",
        "emits",
        "consumes",
        "graphql_queries",
        "graphql_mutations",
        "known_gaps",
        "auth_planes",
        "dependencies",
        "rest_endpoints",
    )
    assert keys[: len(expected_prefix)] == list(expected_prefix)
    assert keys[-1] == "tools"


def test_manifest_drops_empty_catalog_fields_from_wire():
    """Empty catalog fields are omitted to keep the wire payload tight."""
    m = _make_manifest()  # no catalog fields passed
    dumped = m.model_dump_canonical(mode="json")
    for key in CATALOG_FIELD_ORDER:
        assert key not in dumped, f"{key!r} should be dropped when empty"


def test_manifest_preserves_extra_service_specific_fields():
    """Prometheus carries service/protocol/mcp_endpoint — they pass through."""
    m = _make_manifest()
    dumped = m.model_dump_canonical(mode="json")
    # Build a dict directly to simulate service-specific extras:
    raw = dumped | {"service": "Form Service", "protocol": "mcp", "mcp_endpoint": {"port": 4001}}
    canonical = _canonicalise_manifest_dict(raw)
    assert canonical["service"] == "Form Service"
    assert canonical["protocol"] == "mcp"
    assert canonical["mcp_endpoint"] == {"port": 4001}
    # Extras come AFTER tools in the canonical ordering.
    keys = list(canonical.keys())
    assert keys[-3:] == ["service", "protocol", "mcp_endpoint"]


def test_canonicalise_dict_drops_empty_catalog_fields():
    raw = {
        "name": "muse",
        "namespace": "muse",
        "version": "1.0.0",
        "description": "Muse",
        "context": {"domain": "x", "purpose": "y", "bounded_context": "z", "key_entities": [], "aggregates": []},
        "does_not_own": [],
        "emits": ["platform.audit.events"],
        "consumes": [],
        "tools": [],
    }
    canonical = _canonicalise_manifest_dict(raw)
    assert "does_not_own" not in canonical  # empty dropped
    assert "consumes" not in canonical      # empty dropped
    assert canonical["emits"] == ["platform.audit.events"]


def test_create_mcp_server_accepts_dict_manifest():
    """create_mcp_server accepts a pre-built dict (catalog fields included)."""
    from fastapi import FastAPI

    manifest_dict = {
        "name": "muse",
        "namespace": "muse",
        "version": "1.0.0",
        "description": "Muse is the blog service.",
        "context": {
            "domain": "Blog",
            "purpose": "Posts.",
            "bounded_context": "Owns posts.",
            "key_entities": ["Post"],
            "aggregates": ["Post"],
        },
        "emits": ["platform.audit.events"],
        "auth_planes": ["user-jwt", "project-token", "hmac"],
        "tools": [],
    }
    app: FastAPI = create_mcp_server(port=4001, hmac_secret="x" * 32, manifest=manifest_dict, tools=[])
    assert app.title == "Nexus MCP Server"
    assert app.version == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
