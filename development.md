# Development

This guide describes how to set up MCPForge for local development.

## Requirements

- Python 3.11+
- [virtualenv](https://docs.python.org/3/library/venv.html)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the server

Start the MCPForge server locally:

```bash
python run.py
```

The server listens on port 8000 by default.

## Ingesting tools

With the server running, send Python snippets via the `collector.ingest_python` tool.
The selected functions will become new MCP tools available immediately.

