# MCP Usage Guide

This guide explains how to interact with MCPForge using the [Model Context Protocol](https://modelcontextprotocol.org/).

## Starting the Server

1. Ensure Python 3.8+ and an OpenAI API key are available:
   ```bash
   export OPENAI_API_KEY=sk-...
   python run.py
   ```
2. The server listens on `127.0.0.1:8000` by default. Override with `HOST` and `PORT` environment variables.

## Connecting from an MCP Client

MCPForge exposes an SSE endpoint under `/sse`. Point any MCP-compatible client to the server URL:

```
http://<host>:<port>/sse
```

After connecting, the following admin tools are available.

## Available Tools

### `collector.ingest_python`
Ingest a Python snippet and expose selected functions as tools.

- `snippet_name`: label for the snippet (used to name modules)
- `code`: the raw Python source

The server uses `gpt-4.1-nano` to choose safe functions. Newly created tools are registered immediately.

### `collector.list`
Return the names of all registered tool modules.

### `collector.remove`
Remove a registered module by name.

### `forge_health`
Report basic environment and OpenAI connectivity information.

## Typical Workflow

1. Start the server and connect with an MCP client.
2. Call `collector.ingest_python` with a snippet:
   ```json
   {
     "snippet_name": "math utils",
     "code": "def double(x: int) -> int:\n    return x * 2"
   }
   ```
3. Invoke the newly registered tool reported in the response.
4. Use `collector.list` or `collector.remove` to manage registered modules.

