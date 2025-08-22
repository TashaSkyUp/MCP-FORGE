# Features

This document outlines the existing and planned features for MCPForge.

## Existing Features

| Feature | Description | Implementation Date |
| --- | --- | --- |
| Tool Collection from Python Snippets | Ingest Python code snippets and use an LLM to select functions to expose as tools. | 2025-08-21* |
| Dynamic Tool Registration | New tools are registered on the fly without a server restart. | 2025-08-21* |
| Module Management | List and remove collected tool modules. | 2025-08-21* |
| Health Check | A `forge_health` tool to check the server's status. | 2025-08-21* |
| Single Port Operation | Runs over SSE/HTTP on a single port. | 2025-08-21* |
| Customizable Host/Port | Customize host and port via environment variables. | 2025-08-21* |
| Transport Flexibility | Supports `sse`, `http`, and `streamable-http` transports. | 2025-08-21* |

*\*Note: Implementation dates are placeholders. Please update them with the actual dates.*

## Planned Features

### Web-Based Tool Management Interface

**Goal:** Provide a browser-accessible interface to interact with MCPForge and manage tools without using command-line requests.

**Key Capabilities:**

- Create new tools by submitting a Python snippet that is ingested and registered on the server.
- Display a list of currently registered tool modules and allow their removal.
- Show server health status and configuration details.

**Implementation Plan:**

1. **Add web framework and templating support.**
   - Introduce a small FastAPI application served alongside the existing FastMCP server.
   - Use Jinja2 templates to render pages containing forms and lists.
2. **Expose REST endpoints wrapping existing admin tools.**
   - `POST /tools` → wraps `collector.ingest_python` to create new tools.
   - `GET /tools` → wraps `collector.list` to show registered modules.
   - `DELETE /tools/{module}` → wraps `collector.remove` to delete a module.
   - `GET /health` → calls `forge_health`.
3. **Client-side interaction.**
   - Use simple JavaScript or HTMX to submit forms asynchronously and update the page without reloads.
4. **Server integration.**
   - Serve the FastAPI app with Uvicorn on the same host/port configuration as the MCP server.
   - Optionally use HTTPX internally if the web app communicates with the MCP server over HTTP.

**Required Packages:** `fastapi`, `uvicorn`, `jinja2`, `httpx`

**Open Questions / Next Steps:**

- Decide on authentication/authorization for administrative access.
- Determine whether to bundle static assets or rely on CDN links.
