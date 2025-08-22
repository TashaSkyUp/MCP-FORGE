import pytest
import asyncio
from fastmcp import Client

TEST_HOST = "127.0.0.1"
TEST_PORT = 8765


@pytest.mark.asyncio
async def test_list_initial_tools(server):
    """Tests that the collector.list tool returns an empty list when no tools have been ingested."""
    client = Client(f"http://{TEST_HOST}:{TEST_PORT}/sse")

    async with client:
        response = await client.call_tool("collector.list")
        assert response is not None
        assert response.data == []


@pytest.mark.asyncio
@pytest.mark.parametrize("server", [{"USE_MOCK_LLM": "1"}], indirect=True)
async def test_ingest_python_tool(server):
    """Tests that the collector.ingest_python tool can ingest a Python snippet and create a new tool."""
    client = Client(f"http://{TEST_HOST}:{TEST_PORT}/sse")

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
        assert int(add_response.content[0].text) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("server", [{"USE_MOCK_LLM": "1"}], indirect=True)
async def test_ingest_fenced_snippet(server):
    """Ingests a snippet wrapped in Markdown fences."""
    client = Client(f"http://{TEST_HOST}:{TEST_PORT}/sse")

    code_snippet = """Here is a tool:
```python
def add(a: int, b: int) -> int:
    return a + b
```
"""
    snippet_name = "fenced"

    async with client:
        response = await client.call_tool(
            "collector.ingest_python", {"snippet_name": snippet_name, "code": code_snippet}
        )
        assert response is not None
        assert len(response.data.get("created", [])) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "server",
    [
        {
            "USE_MOCK_LLM": "1",
            "MOCK_LLM_SNIPPET": "def multiply(a: int, b: int) -> int:\n    return a * b",
            "MOCK_LLM_FUNCTION": "multiply",
        }
    ],
    indirect=True,
)
async def test_ingest_ambiguous_snippet(server):
    """Delegates vague text to GPT to construct code."""
    client = Client(f"http://{TEST_HOST}:{TEST_PORT}/sse")

    snippet_name = "ambiguous"
    code_snippet = "multiply two numbers"

    async with client:
        response = await client.call_tool(
            "collector.ingest_python", {"snippet_name": snippet_name, "code": code_snippet}
        )
        assert response is not None
        assert len(response.data.get("created", [])) == 1

        tool_response = await client.call_tool("multiply", {"a": 2, "b": 3})
        assert tool_response is not None
        assert int(tool_response.content[0].text) == 6


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "server",
    [
        {
            "USE_MOCK_LLM": "1",
            "MOCK_LLM_SNIPPET": "def organic_growth(initial: float, rate: float, periods: int) -> float:\n    return initial * (1 + rate) ** periods",
            "MOCK_LLM_FUNCTION": "organic_growth",
        }
    ],
    indirect=True,
)
async def test_ingest_exponential_growth_snippet(server):
    """Generates an exponential growth function from descriptive text."""
    client = Client(f"http://{TEST_HOST}:{TEST_PORT}/sse")

    snippet_name = "No Clue"
    code_snippet = "I need a function that calculates exponential organic growth"

    async with client:
        response = await client.call_tool(
            "collector.ingest_python", {"snippet_name": snippet_name, "code": code_snippet}
        )
        assert response is not None
        assert len(response.data.get("created", [])) == 1

        growth_response = await client.call_tool(
            "organic_growth", {"initial": 100, "rate": 0.05, "periods": 10}
        )
        assert growth_response is not None
        assert float(growth_response.content[0].text) == pytest.approx(162.8894626777442)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "server", [{"USE_MOCK_LLM": "1", "MOCK_LLM_FUNCTION": "subtract"}], indirect=True
)
async def test_remove_tool(server):
    """Tests that a tool can be ingested and then removed."""
    client = Client(f"http://{TEST_HOST}:{TEST_PORT}/sse")

    code_snippet = """

def subtract(a: int, b: int) -> int:
    return a - b
"""
    snippet_name = "test_sub_snippet"

    async with client:
        ingest_response = await client.call_tool(
            "collector.ingest_python", {"snippet_name": snippet_name, "code": code_snippet}
        )
        assert ingest_response is not None
        assert "created" in ingest_response.data
        assert len(ingest_response.data["created"]) == 1
        module_name = ingest_response.data["created"][0]

        # Verify that the new tool is listed
        list_response = await client.call_tool("collector.list")
        assert list_response is not None
        assert module_name in list_response.data

        # Verify that the new tool can be called
        tool_name = "subtract"
        sub_response = await client.call_tool(tool_name, {"a": 5, "b": 3})
        assert sub_response is not None
        assert int(sub_response.content[0].text) == 2

        # Remove the tool
        remove_response = await client.call_tool("collector.remove", {"module_name": module_name})
        assert remove_response.data is True

        # Verify that the tool is no longer listed
        list_response_after_remove = await client.call_tool("collector.list")
        assert list_response_after_remove is not None
        assert module_name not in list_response_after_remove.data

        # Verify that calling the removed tool fails
        from fastmcp.exceptions import ToolError
        with pytest.raises(ToolError, match="Unknown tool: subtract"):
            await client.call_tool(tool_name, {"a": 5, "b": 3})
