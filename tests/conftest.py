import os
import time
import shutil
import subprocess
import pytest

TEST_HOST = "127.0.0.1"
TEST_PORT = 8765

@pytest.fixture(autouse=True)
def clean_registry():
    """A fixture to clean the registry directory before each test."""
    if os.path.isdir("registry"):
        shutil.rmtree("registry")


@pytest.fixture(scope="function")
def server(request):
    """Run the MCPForge server as a subprocess for tests."""
    env = os.environ.copy()
    env["HOST"] = TEST_HOST
    env["PORT"] = str(TEST_PORT)
    env["MCP_TRANSPORT"] = "sse"

    if hasattr(request, "param"):
        env.update(request.param)

    # Clean up the registry directory before starting the server
    if os.path.exists("./registry"):
        shutil.rmtree("./registry")
    os.makedirs("./registry")

    server_process = subprocess.Popen(
        ["python", "run.py"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Give the server a moment to start up
    time.sleep(2)

    yield

    # Teardown: terminate the server process
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()
