"""Pydantic models aligned with nexus-mcp-contract schemas.

The optional catalog fields on `Manifest` (does_not_own, emits, consumes,
graphql_queries, graphql_mutations, known_gaps, auth_planes,
dependencies, rest_endpoints) carry the additional context the Nexus
frontend renders alongside the service description. They are all
optional so the SDK remains backwards-compatible with services that
haven't yet been upgraded to emit them.

Field serialization order matches mercury's manifest contract so the
Nexus aggregator can render catalogs uniformly.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolAnnotation(BaseModel):
    """Optional behavioural annotations for a tool."""

    read_only: bool | None = Field(default=None, alias="readOnly")
    destructive: bool | None = None

    model_config = ConfigDict(populate_by_name=True)


class MCPToolDefinition(BaseModel):
    """Schema for a single tool exposed through the Nexus MCP ecosystem."""

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(min_length=20)
    input_schema: dict[str, Any] = Field(alias="inputSchema")
    annotations: ToolAnnotation | None = None

    model_config = ConfigDict(populate_by_name=True)


class ManifestContext(BaseModel):
    """DDD context metadata."""

    domain: str
    purpose: str
    bounded_context: str = Field(alias="bounded_context")
    key_entities: list[str] = Field(alias="key_entities")
    aggregates: list[str]

    model_config = ConfigDict(populate_by_name=True)


# Canonical order for catalog fields. Matches the order used by every
# Nexus service's manifest.json on disk and the order the Nexus aggregator
# expects when it renders the catalog UI.
CATALOG_FIELD_ORDER: tuple[str, ...] = (
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


class Manifest(BaseModel):
    """Describes a Nexus service's domain context and the tools it exposes via MCP.

    Catalog fields (does_not_own, emits, consumes, graphql_queries,
    graphql_mutations, known_gaps, auth_planes, dependencies,
    rest_endpoints) are all optional. Each can be passed positionally
    as a keyword argument. Unknown fields are allowed so services can
    carry service-specific extras without bumping the SDK for every
    addition.
    """

    name: str
    namespace: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    version: str = Field(pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*).*$")
    description: str
    context: ManifestContext
    tools: list[MCPToolDefinition]

    # Catalog fields — typed explicitly so consumers get autocompletion
    # and Ajv-compatible validation, while still being optional. The
    # generic extra="allow" lets services pass extra service-specific
    # fields without bumping the SDK.
    does_not_own: list[str] = Field(default_factory=list)
    emits: list[str] = Field(default_factory=list)
    consumes: list[str] = Field(default_factory=list)
    graphql_queries: list[str] = Field(default_factory=list)
    graphql_mutations: list[str] = Field(default_factory=list)
    known_gaps: list[str] = Field(default_factory=list)
    auth_planes: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    rest_endpoints: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(
        populate_by_name=True,
        # Allow unknown fields so services can carry service-specific
        # extras (e.g. prometheus's `service`/`protocol`/`mcp_endpoint`)
        # without bumping the SDK for every addition.
        extra="allow",
    )

    def model_dump_canonical(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize in mercury's canonical key order.

        Field order:
            name, namespace, version, description, context,
            does_not_own, emits, consumes,
            graphql_queries, graphql_mutations,
            known_gaps, auth_planes, dependencies, rest_endpoints,
            tools,
            <any extra fields in declaration order>

        Empty catalog fields are dropped from the wire payload — the
        Nexus aggregator treats missing == empty.
        """
        dumped = super().model_dump(**kwargs)
        out: dict[str, Any] = {}

        # 1. Typed base fields in declared order.
        for key in ("name", "namespace", "version", "description", "context"):
            if key in dumped:
                out[key] = dumped.pop(key)

        # 2. Catalog fields in canonical order — only when non-empty.
        for key in CATALOG_FIELD_ORDER:
            if key in dumped:
                value = dumped.pop(key)
                if value:  # skip empty lists / dicts
                    out[key] = value

        # 3. tools.
        if "tools" in dumped:
            out["tools"] = dumped.pop("tools")

        # 4. Anything else (service-specific extras) goes at the end
        #    in the order Pydantic produced them. Skip empty catalog
        #    fields (already dropped above).
        for key, value in dumped.items():
            if key in out:
                continue
            if key in CATALOG_FIELD_ORDER and not value:
                continue
            out[key] = value

        return out
