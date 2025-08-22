import pytest
import asyncio
from fastmcp import Client

# The OpenAI API key is required to run the server.
# The tests will fail if the OPENAI_API_KEY environment variable is not set.
# You can set it by running `export OPENAI_API_KEY='your-key'` in your terminal.

TEST_HOST = "127.0.0.1"
TEST_PORT = 8765


@pytest.mark.asyncio
async def test_forge_health(server):
    """
    Tests that the forge_health tool is available and returns a successful response.
    """
    client = Client(f"http://{TEST_HOST}:{TEST_PORT}/sse")

    async with client:
        response = await client.call_tool("forge_health")
        assert response is not None
        # The health check returns a dictionary with server info.
        assert isinstance(response.data, str)
        assert "ok" in response.data
