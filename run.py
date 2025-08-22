"""
Run the MCP Forge tool collector.
"""

def main():
    def _impl():
        import argparse
        from app.server import main as _run
        parser = argparse.ArgumentParser(description="Run the MCP Forge tool collector server.")
        parser.add_argument("--host", type=str, default=None, help="Host to bind the server to.")
        parser.add_argument("--port", type=int, default=None, help="Port to bind the server to.")
        args = parser.parse_args()
        _run(host=args.host, port=args.port)
    return _impl()

if __name__ == "__main__":
    main()
