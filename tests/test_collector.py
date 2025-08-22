import pytest
import asyncio
from fastmcp import Client

# The OpenAI API key is required to run the server.
# The tests will fail if the OPENAI_API_KEY environment variable is not set.
# You can set it by running `export OPENAI_API_KEY='your-key'` in your terminal.

TEST_HOST = "127.0.0.1"
TEST_PORT = 8765


@pytest.mark.asyncio
async def test_list_initial_tools(server):
    """
    Tests that the collector.list tool returns an empty list when no tools have been ingested.
    """
    client = Client(f"http://{TEST_HOST}:{TEST_PORT}/sse")

    async with client:
        response = await client.call_tool("collector.list")
        assert response is not None
        assert response.data == []

@pytest.mark.asyncio
async def test_ingest_python_tool(server, monkeypatch):
    """
    Tests that the collector.ingest_python tool can ingest a Python snippet and create a new tool.
    """
    client = Client(f"http://{TEST_HOST}:{TEST_PORT}/sse")

    # Mock the choose_tools_with_gpt function to avoid calling the OpenAI API
    def mock_choose_tools(*args, **kwargs):
        return [{"original_name": "add", "tool_name": "add", "description": "Adds two numbers."}]

    monkeypatch.setattr("app.server.choose_tools_with_gpt", mock_choose_tools)

    code_snippet = """
def add(a: int, b: int) -> int:
    return a + b
"""
    snippet_name = "test_snippet"

    async with client:
        response = await client.call_tool(
            "collector.ingest_python", {"snippet_name": snippet_name, "code": code_snippet}
        )
        assert response is not None
        assert "created" in response.data
        assert len(response.data["created"]) == 1

        # Verify that the new tool is listed
        list_response = await client.call_tool("collector.list")
        assert list_response is not None
        assert snippet_name in list_response.data[0]

        # Verify that the new tool can be called
        tool_name = "add"
        add_response = await client.call_tool(tool_name, {"a": 1, "b": 2})
        assert add_response is not None
        assert add_response.data == 3
