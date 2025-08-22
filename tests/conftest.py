import os
import time
import shutil
import subprocess
import pytest

TEST_HOST = "127.0.0.1"
TEST_PORT = 8765

@pytest.fixture(scope="function")
def server(request):
    """A pytest fixture to run the MCPForge server as a subprocess."""
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

    # Start the server as a subprocess
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
