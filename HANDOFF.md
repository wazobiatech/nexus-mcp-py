# ZIN-4662 — wazobiatech-nexus-mcp (Python SDK) Handoff

## Status: 🔍 Review

Blocking PR review issues resolved. Deferred design decisions documented below.

---

## Fixes Applied

### ✅ Middleware query string bug — FIXED
- **File:** `nexus_mcp/middleware.py`
- Was using `request.url.path` which strips query string
- Now builds full path: `path + "?" + query` when query string present
- HMAC signatures now match for URLs like `/mcp/manifest?v=1`

### ✅ `HMACClient` — IMPLEMENTED
- **File:** `nexus_mcp/client.py` (new)
- Async `httpx`-based client that auto-signs every outbound request
- `get(path)` and `post(path)` both inject `x-signature` / `x-timestamp` headers
- Supports async context manager (`async with HMACClient(...) as client`)
- Exported from `nexus_mcp/__init__.py`
- Required by ZIN-4655-T2 (`mcp_protocol/hmac_client.py` in the aggregator)

### ✅ Middleware wiring — FIXED
- **File:** `nexus_mcp/server.py`
- Was: `app.add_middleware(BaseHTTPMiddleware, dispatch=HMACMiddleware(app, ...).dispatch)` (hacky)
- Now: `app.add_middleware(HMACMiddleware, hmac_secret=hmac_secret)` (correct Starlette pattern)

### ✅ Tool handler now called — FIXED
- **File:** `nexus_mcp/server.py`
- Was returning a placeholder `{"result": {"tool": ..., "arguments": ...}}`
- Now calls `await tool.handler(arguments)` and returns the result
- Raises `501` if a tool has no callable handler

### ✅ `.pypirc` removed from repo
- Deleted via `git rm .pypirc`
- Added `.pypirc` to `.gitignore`
- CI uses `POETRY_PYPI_TOKEN_WAZOBIA` env secret — no file needed

### ✅ `httpx` moved to main dependencies
- **File:** `pyproject.toml`
- `httpx` was in `[dev.dependencies]` but `HMACClient` is a runtime export
- Moved to `[tool.poetry.dependencies]`

---

## What Was Already Correct

- `sign_request(method, path, secret) -> (x_signature, x_timestamp)` — stdlib only ✅
- `hmac.compare_digest()` timing-safe comparison ✅
- All 4 middleware unit tests (valid, bad sig, stale, missing headers) ✅
- 16 contract vector tests against `nexus-mcp-contract v1.0.0` ✅
- Pydantic `MCPToolDefinition` and `Manifest` models aligned with contract schemas ✅
- CI: ruff → vectors → pytest → `poetry publish` on tag ✅
- `pyproject.toml` Python `^3.11`, package name `wazobiatech-nexus-mcp` ✅

---

## Open / Deferred (not blockers)

- **Body not signed**: `POST /mcp/call` arguments aren't covered by HMAC. Replay possible within 300s window. Acceptable for internal mesh — needs explicit decision in contract if intentional.
- **No server-side inputSchema validation**: arguments passed straight to handler. Could validate against `input_schema` cheaply since Pydantic is already a dependency.
- **`.pypirc` history**: if `.pypirc` ever held a real token in a prior commit, rotate the credential — `git rm` doesn't purge git history.

## Before Tagging

1. Set `WAZOBIA_PYPI_URL` and `WAZOBIA_PYPI_TOKEN` as Bitbucket repo variables.
2. Tag `v1.0.0` and push — Bitbucket pipeline will run lint → test → publish automatically.
