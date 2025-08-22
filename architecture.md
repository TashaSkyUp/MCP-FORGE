# MCPForge Architecture

## Overview
MCPForge is a tool-collector server built with the Model Context Protocol and FastMCP. Users submit Python snippets, and the system selects safe functions to expose as tools. The server and a web-based management interface share a single HTTP/SSE port.

## Entry Point
- `run.py` defines a `main` function that parses optional `--host` and `--port` arguments and delegates to `app.server.main` to start the combined server.

## Core Packages

### `app.__init__`
- Provides a minimal `version()` function returning `"0.1.0"`.

### `app.server`
- Implements the main server logic.
- `_parse_functions(code)` uses the `ast` module to extract top-level function names, docstrings, argument annotations, and return annotations from a snippet.
- `build_server()` constructs a `FastMCP` instance and registers administrative tools:
  - `collector.list` — returns the currently registered module names.
  - `collector.remove` — removes a module file and unregisters its tool.
  - `collector.ingest_python` — parses a snippet, consults the LLM selector, writes tool modules under `./registry`, and loads them.
  - `forge_health` — reports Python version, operating system, and OpenAI connectivity status.
- `build_app()` wraps the MCP server in a FastAPI application:
  - `/health` returns the output of `forge_health`.
  - `/tools` supports `GET` (list), `POST` (ingest), and `DELETE /tools/{module}` (remove).
  - `/` serves an HTML interface rendered from `app/templates/index.html`.
  - The MCP SSE server is mounted at `/sse`.
- `main(host, port)` runs the FastAPI app with Uvicorn, defaulting to environment variables `HOST` and `PORT` if arguments are absent.

### `app.registry`
- Handles persistence of generated tool modules in the `./registry` directory.
- `_get_tool_name_from_source(path)` reads a module file to determine the tool name from its decorator.
- `ensure_dirs(base_dir)` creates the registry directory.
- `safe_mod_name(name)` sanitizes snippet labels into valid module names.
- `write_tool_module(...)` generates a module containing a `register(mcp)` function. The wrapper executes the original snippet in an isolated namespace and registers the target function as an MCP tool.
- `load_all_registered(mcp, base_dir)` imports every module in the registry and calls its `register` function, returning a map of module names to tool names.
- `delete_tool_module(base_dir, module_name)` removes a stored module file.

### `app.llm`
- `choose_tools_with_gpt(code, fn_summaries)` interacts with OpenAI's `gpt-4.1-nano` model to pick functions to expose. It supports a mock mode via `USE_MOCK_LLM` for tests.

### Templates
- `app/templates/index.html` defines the web interface. It uses [htmx](https://htmx.org/) to submit snippets and manage registered modules without page reloads.

## Tests
- Pytest fixtures in `tests/conftest.py` launch the server as a subprocess and clean the `registry` directory between tests.
- `tests/test_server.py` verifies the `forge_health` tool.
- `tests/test_collector.py` checks tool ingestion, listing, and removal using the mock LLM.
- `tests/test_web_ui.py` exercises the REST endpoints and template-driven UI.

## Dependencies
- `requirements.txt` lists runtime and testing dependencies, including `fastmcp`, `openai`, `fastapi`, `uvicorn`, `jinja2`, `httpx`, and `pytest`.

## Documentation
- Additional guides: `development.md`, `testing.md`, `usage-mcp.md`, and `usage-ui.md` describe setup, testing, and usage from MCP clients or the web interface.

## User Input Ingestion
- **Detect LLM-formatted submissions:** When a user paste includes narrative text followed by a fenced code block (e.g., Markdown ```python fences), the server strips the fences and uses only the code segment.
- **Accept clean snippets:** If the resulting text parses successfully with the `ast` module, the snippet is treated as ready-to-use code and normal ingestion proceeds.
- **Delegate ambiguous input to GPT-4.1-nano:** For any other cases—such as incomplete or pseudocode snippets—the server invokes `gpt-4.1-nano` to rewrite the snippet into valid Python before attempting registration.
