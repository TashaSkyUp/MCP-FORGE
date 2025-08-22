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

## Documentation

- [Development guide](development.md)
- [Testing guide](testing.md)

## License

This project is provided as an example and is licensed under the MIT License.
