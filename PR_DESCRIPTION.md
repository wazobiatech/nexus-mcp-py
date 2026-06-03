# 📌 Summary

Implements the **Python SDK** for the Nexus MCP ecosystem (ZIN-4662).  
This package (`wazobiatech-nexus-mcp`) provides HMAC-SHA256 request signing/verification, MCP server scaffolding, and Pydantic manifest/tool models so that Python Nexus services (e.g. the Aggregator) do not re-implement HMAC logic themselves.

---

# 🛠️ Type of Change

Select all that apply:

- [ ] 🐛 Bug fix (fixes an issue)
- [x] ✨ New feature (adds functionality)
- [ ] 💥 Breaking change (changes existing functionality)
- [x] 📖 Documentation update
- [ ] 🔧 Refactoring (code improvement without changing functionality)
- [ ] 🚀 Performance improvement
- [x] ✅ Test enhancement
- [x] 🏗️ Build/configuration change

---

# 🔄 Changes Made

- `nexus_mcp/hmac_utils.py` — `sign_request()` with byte-for-byte payload construction and full docstring
- `nexus_mcp/middleware.py` — `HMACMiddleware` (Starlette `BaseHTTPMiddleware`) with `hmac.compare_digest`
- `nexus_mcp/models.py` — Pydantic `MCPToolDefinition`, `Manifest`, and `ManifestContext` models aligned with contract schemas
- `nexus_mcp/server.py` — `create_mcp_server()` FastAPI factory with HMAC middleware wired
- `tests/test_hmac_utils.py` — contract vector test suite (16 vectors from `nexus-mcp-contract v1.0.0`)
- `tests/test_middleware.py` — unit tests for valid ✅ / bad sig ❌ / stale ❌ / missing headers ❌
- `bitbucket-pipelines.yml` — ruff lint, contract vectors, pytest, and Poetry publish to private PyPI on `v*` tag (`.github/workflows/ci.yml` deleted — this repo lives on Bitbucket)
- `.pypirc` — removed from repo; added to `.gitignore`; CI uses `WAZOBIA_PYPI_TOKEN` + `WAZOBIA_PYPI_URL` Bitbucket repo variables

---

# 🧪 Testing

- [x] Contract vector tests — all 16 canonical HMAC vectors from `nexus-mcp-contract` pass
- [x] Unit tests for HMAC middleware (valid ✅, bad sig ❌, stale timestamp ❌, missing headers ❌)
- [x] Ruff linting passes
- [x] Manual smoke test locally
- [ ] Integration tests added/updated
- [ ] End-to-end (E2E) tests added/updated

---

# 🧩 Test Environment

- [x] Local development
- [ ] Staging
- [ ] Production
- [ ] Other (specify):

---

# 📸 Screenshots / Demos

N/A — No UI redesign

---

# 🔗 Related Issues / Tickets

- **Blocks:** ZIN-4655-T2/T3 (Aggregator manifest federation & tool routing)
- **Blocked by:** ZIN-4660 (nexus-mcp-contract v1.0.0)

---

# 📝 Release Notes (for tag `v1.0.0`)

- HMAC-SHA256 signing utility (`sign_request`)
- FastAPI/Starlette HMAC middleware (`HMACMiddleware`)
- Pydantic models for `MCPToolDefinition` and `Manifest`
- MCP server factory (`create_mcp_server`)
- Full contract vector test coverage

---

# ✅ Pre-merge Checklist

- [x] CI passes (ruff + pytest + contract vectors)
- [x] Contract vector tests pass against `nexus-mcp-contract v1.0.0`
- [x] README updated with install/usage examples
- [x] Version bumped to `1.0.0`
- [ ] SDK team review sign-off
