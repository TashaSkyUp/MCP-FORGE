import pytest
import httpx

TEST_HOST = "127.0.0.1"
TEST_PORT = 8765
BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}"

pytestmark = pytest.mark.xfail(reason="Web UI endpoints not yet implemented")


@pytest.mark.asyncio
async def test_health_endpoint(server):
    """The planned /health endpoint should return server status."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/health")
        assert resp.status_code == 200
        assert "ok" in resp.text.lower()


@pytest.mark.asyncio
async def test_tool_lifecycle(server):
    """End-to-end tool creation, listing, and deletion via planned HTTP endpoints."""
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

        # The tool should appear in the list
        resp = await client.get(f"{BASE_URL}/tools")
        assert resp.status_code == 200
        assert module_name in resp.json()

        # Remove the tool
        resp = await client.delete(f"{BASE_URL}/tools/{module_name}")
        assert resp.status_code == 200

        # Verify removal
        resp = await client.get(f"{BASE_URL}/tools")
        assert resp.status_code == 200
        assert module_name not in resp.json()
