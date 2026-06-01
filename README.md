# wazobiatech-nexus-mcp

Python SDK for the Nexus MCP ecosystem. Provides HMAC signing/verification and MCP server scaffolding.

## Installation

```bash
pip install wazobiatech-nexus-mcp
```

## Usage

### HMAC Signing

```python
from nexus_mcp.hmac_utils import sign_request

sig, ts = sign_request("GET", "/mcp/manifest", "my-secret")
print("x-signature:", sig)
print("x-timestamp:", ts)
```

### HMAC Middleware (FastAPI)

```python
from fastapi import FastAPI
from nexus_mcp.middleware import HMACMiddleware

app = FastAPI()
app.add_middleware(HMACMiddleware, hmac_secret="my-secret")
```

### MCP Server

```python
from nexus_mcp.server import create_mcp_server
from nexus_mcp.models import Manifest

app = create_mcp_server(
    port=8000,
    hmac_secret="my-secret",
    manifest=Manifest(...),
    tools=[...],
)

# Start with uvicorn
# uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Testing

```bash
poetry install
poetry run pytest
```

Contract vector tests verify every entry from `nexus-mcp-contract/vectors.json`.

## License

MIT
