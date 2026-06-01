"""Pydantic models aligned with nexus-mcp-contract schemas."""

from typing import Any
from pydantic import BaseModel, Field


class ToolAnnotation(BaseModel):
    """Optional behavioural annotations for a tool."""

    read_only: bool | None = Field(default=None, alias="readOnly")
    destructive: bool | None = None

    model_config = {"populate_by_name": True}


class MCPToolDefinition(BaseModel):
    """Schema for a single tool exposed through the Nexus MCP ecosystem."""

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(min_length=20)
    input_schema: dict[str, Any] = Field(alias="inputSchema")
    annotations: ToolAnnotation | None = None

    model_config = {"populate_by_name": True}


class ManifestContext(BaseModel):
    """DDD context metadata."""

    domain: str
    purpose: str
    bounded_context: str = Field(alias="bounded_context")
    key_entities: list[str] = Field(alias="key_entities")
    aggregates: list[str]

    model_config = {"populate_by_name": True}


class Manifest(BaseModel):
    """Describes a Nexus service's domain context and the tools it exposes via MCP."""

    name: str
    namespace: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    version: str = Field(pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*).*$")
    description: str
    context: ManifestContext
    tools: list[MCPToolDefinition]
