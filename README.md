<!--- README for MCPForge -->

# MCPForge

MCPForge is a tool‑collector server built using the [Model Context Protocol](https://modelcontextprotocol.org/)
and [FastMCP](https://github.com/modelcontextprotocol/fastmcp).
It allows you to paste arbitrary Python snippets and have an LLM decide which functions
are safe and useful to expose as tools.  The server runs on a single HTTP/SSE port, and
dynamically registers new tools on the fly.

## Features

- Collect tools from Python snippets: call the `collector.ingest_python` tool with a label
  and code text to curate functions with the help of `gpt-4.1-nano`.  Selected functions
  become new MCP tools and are registered immediately.
- List collected modules with `collector.list` and remove them with `collector.remove`.
- Health check via `forge_health`.
- Runs over SSE/HTTP on a single port (default 8000) — no need to allocate extra ports.
- All imports in this package occur inside function bodies to comply with
  user preferences.
- Web-based management UI and REST endpoints for creating, listing, and
  removing tools.

## Requirements

- Python 3.8 or later.
- An [OpenAI API key](https://platform.openai.com/account/api-keys) with
  access to the `gpt-4.1-nano` model.  Set it in the environment variable
  `OPENAI_API_KEY` before running.

Install dependencies using pip:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
```

## Running

To start the server on the default host and port (127.0.0.1:8000):

```bash
python run.py
```

You can customise the host/port via environment variables:

```bash
HOST=0.0.0.0 PORT=8765 python run.py
```

The web interface and REST endpoints are served from the root URL. The MCP
server is available on the `/sse` path for SSE clients.

## Ingesting Code

Use an MCP client (for example, Zed or `mcp-remote`) to call the `collector.ingest_python`
tool.  Provide two arguments:

- `snippet_name`: a descriptive label for your snippet (used to name generated modules).
- `code`: the raw Python code containing one or more functions.

The server will call `gpt-4.1-nano` to decide which functions to expose as tools.
If none are deemed safe/appropriate, the first function will be exposed by default.
Newly registered tools become available immediately and are prefixed by the snippet name.

## License

This project is provided as an example and is licensed under the MIT License.
