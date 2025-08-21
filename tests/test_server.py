import os
import time
import threading
import pytest
import asyncio
from fastmcp import Client
from mcpforge.server import main as server_main

# The OpenAI API key is required to run the server.
# The tests will fail if the OPENAI_API_KEY environment variable is not set.
# You can set it by running `export OPENAI_API_KEY='your-key'` in your terminal.

TEST_HOST = "127.0.0.1"
TEST_PORT = 8765

@pytest.fixture(scope="module")
def server():
    """A pytest fixture to run the MCPForge server in a background thread."""
    os.environ["HOST"] = TEST_HOST
    os.environ["PORT"] = str(TEST_PORT)
    os.environ["MCP_TRANSPORT"] = "sse"

    server_thread = threading.Thread(target=server_main)
    server_thread.daemon = True
    server_thread.start()

    # Give the server a moment to start up
    time.sleep(2)

    yield

    # Teardown: The daemon thread will be killed when the main thread exits.

@pytest.mark.asyncio
async def test_forge_health(server):
    """
    Tests that the forge_health tool is available and returns a successful response.
    """
    client = Client(f"http://{TEST_HOST}:{TEST_PORT}/mcp")

    async with client:
        response = await client.call_tool("forge_health")
        assert response is not None
        # The health check returns a dictionary with server info.
        assert isinstance(response.data, dict)
        assert "server_name" in response.data
        assert response.data["server_name"] == "mcp-forge"
