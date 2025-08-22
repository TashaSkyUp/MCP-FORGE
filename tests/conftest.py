import os
import time
import threading
import pytest
from app.server import main as server_main

TEST_HOST = "127.0.0.1"
TEST_PORT = 8765

@pytest.fixture(scope="session")
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
