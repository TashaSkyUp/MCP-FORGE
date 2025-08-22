import pytest
import httpx

TEST_HOST = "127.0.0.1"
TEST_PORT = 8765
BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}"


@pytest.mark.asyncio
async def test_health_endpoint(server):
    """The /health endpoint should return server status."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/health")
        assert resp.status_code == 200
        assert "ok" in resp.text.lower()


@pytest.mark.asyncio
async def test_tool_lifecycle(server):
    """End-to-end tool creation, listing, and deletion via HTTP endpoints."""
    code_snippet = """
    def add(a: int, b: int) -> int:
        return a + b
    """
    async with httpx.AsyncClient() as client:
        # Initially, no tools should be registered
        resp = await client.get(f"{BASE_URL}/tools")
        assert resp.status_code == 200
        assert resp.json() == []

        # Ingest a new tool
        resp = await client.post(
            f"{BASE_URL}/tools",
            json={"snippet_name": "test_snippet", "code": code_snippet},
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert "created" in data and data["created"]
        module_name = data["created"][0]

        # Example parameters should be stored on disk
        import json, os
        with open(os.path.join("registry", f"{module_name}.json"), "r", encoding="utf-8") as f:
            meta = json.load(f)
        assert "example_params" in meta and meta["example_params"]

        # The tool should appear in the list
        resp = await client.get(f"{BASE_URL}/tools")
        assert resp.status_code == 200
        assert module_name in resp.json()

        # Test the tool using stored example parameters
        resp = await client.post(f"{BASE_URL}/tools/{module_name}/test")
        assert resp.status_code == 200
        data = resp.json()
        assert int(data["output"]["result"]) == 3

        # Remove the tool
        resp = await client.delete(f"{BASE_URL}/tools/{module_name}")
        assert resp.status_code == 200

        # Verify removal
        resp = await client.get(f"{BASE_URL}/tools")
        assert resp.status_code == 200
        assert module_name not in resp.json()
