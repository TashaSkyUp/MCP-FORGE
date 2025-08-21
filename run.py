"""
Run the MCP Forge tool collector.
"""

def main():
    def _impl():
        from mcpforge.server import main as _run
        _run()
    return _impl()

if __name__ == "__main__":
    main()