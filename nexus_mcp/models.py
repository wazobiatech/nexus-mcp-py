"""Pydantic models aligned with nexus-mcp-contract schemas."""

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema

# Type alias keeps the handler field declaration under the 100-char line limit.
HandlerFn = SkipJsonSchema[Callable[..., Awaitable[Any]] | None]


class ToolAnnotation(BaseModel):
    """Optional behavioural annotations for a tool."""

    read_only: bool | None = Field(default=None, alias="readOnly")
    destructive: bool | None = None

    model_config = {"populate_by_name": True}


class MCPToolDefinition(BaseModel):
    """Schema for a single tool exposed through the Nexus MCP ecosystem.

    The ``handler`` field carries the callable invoked at runtime and is
    excluded from all serialized output (manifest JSON, wire format).
    This mirrors the TypeScript SDK's ``Omit<MCPToolDefinition, 'handler'>``
    pattern for manifest generation.
    """

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(min_length=20)
    input_schema: dict[str, Any] = Field(alias="inputSchema")
    annotations: ToolAnnotation | None = None
    # Handler is excluded from JSON/OpenAPI output — never appears in manifest or wire format.
    # SkipJsonSchema prevents PydanticInvalidForJsonSchema when model_json_schema() is called
    # directly (FastAPI's tolerant path hides this; direct calls would blow up without it).
    handler: HandlerFn = Field(default=None, exclude=True)

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}


class ManifestContext(BaseModel):
    """DDD context metadata."""

    domain: str
    purpose: str
    # Contract JSON uses snake_case — aliases are not needed here.
    bounded_context: str
    key_entities: list[str]
    aggregates: list[str]


class Manifest(BaseModel):
    """Describes a Nexus service's domain context and the tools it exposes via MCP."""

    name: str
    namespace: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    version: str = Field(pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*).*$")
    description: str
    context: ManifestContext
    tools: list[MCPToolDefinition]
