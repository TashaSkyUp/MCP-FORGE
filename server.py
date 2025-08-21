"""
Entry points for the MCPForge tool collector server.

This module builds a FastMCP server that exposes three admin tools for
managing collected tools:

* ``collector.list`` – list the registered modules.
* ``collector.remove`` – delete a registered module.
* ``collector.ingest_python`` – ingest a snippet; the server uses GPT‑4.1‑nano
  to decide which functions to expose as tools and auto‑registers them.

It also exposes a ``forge_health`` tool to check the server health.
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any

def _parse_functions(code: str) -> List[Dict[str, Any]]:
    """Parse top-level functions in a Python snippet to extract signatures."""
    def _impl() -> List[Dict[str, Any]]:
        import ast
        import inspect
        tree = ast.parse(code)
        out: List[Dict[str, Any]] = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                name = node.name
                doc = ast.get_docstring(node) or ""
                args: List[Tuple[str, str]] = []
                for a in node.args.args:
                    ann = None
                    if a.annotation is not None:
                        try:
                            ann = inspect.getsource(ast.fix_missing_locations(a.annotation))
                        except Exception:
                            ann = None
                    args.append((a.arg, (ann or "str")))
                out.append({"name": name, "doc": doc, "args": args})
        return out
    return _impl()

def build_server():
    """Construct and return the FastMCP server configured with admin tools."""
    def _impl():
        from fastmcp import FastMCP
        from .registry import ensure_dirs, load_all_registered, write_tool_module, safe_mod_name, delete_tool_module
        from .llm import choose_tools_with_gpt

        REG_DIR = ensure_dirs("./registry")
        mcp = FastMCP("MCPForge (single port)")

        @mcp.tool(name="collector.list", description="List collected tool modules currently registered.")
        def list_collected() -> List[str]:
            import os
            names = []
            if os.path.isdir(REG_DIR):
                for fn in sorted(os.listdir(REG_DIR)):
                    if fn.endswith(".py"):
                        names.append(fn[:-3])
            return names

        @mcp.tool(name="collector.remove", description="Remove a collected tool module by module name (not tool name).")
        def remove_collected(module_name: str) -> bool:
            ok = delete_tool_module(REG_DIR, module_name)
            return ok

        @mcp.tool(name="collector.ingest_python", description="Ingest a Python snippet and expose chosen functions as tools.")
        def ingest_python(snippet_name: str, code: str) -> Dict[str, Any]:
            funcs = _parse_functions(code)
            if not funcs:
                return {"created": [], "reason": "no functions found"}
            summaries = [{"name": f["name"], "doc": f["doc"], "args": f["args"]} for f in funcs]
            chosen = choose_tools_with_gpt(code, summaries)
            if not chosen:
                f0 = funcs[0]
                chosen = [{
                    "original_name": f0["name"],
                    "tool_name": f0["name"],
                    "description": (f0["doc"] or "No description.")[:120]
                }]
            created: List[str] = []
            base = safe_mod_name(snippet_name)
            idx = 1
            for c in chosen:
                orig = c.get("original_name")
                tname = c.get("tool_name") or orig
                desc = c.get("description") or f"{orig} tool"
                arg_spec = next((f["args"] for f in funcs if f["name"] == orig), [])
                mod_name = f"{base}_{idx}"
                write_tool_module("./registry", mod_name, code, orig, tname, desc, arg_spec)
                created.append(mod_name)
                idx += 1
            load_all_registered(mcp, "./registry")
            return {"created": created}

        @mcp.tool(name="forge_health", description="Health check for the MCP Forge server.")
        def forge_health() -> str:
            import platform
            import sys
            return f"ok | py={sys.version.split()[0]} | os={platform.system()}"

        load_all_registered(mcp, "./registry")
        return mcp
    return _impl()

def main():
    """Run the server using SSE on a single port."""
    def _impl():
        import os
        mcp = build_server()
        host = os.getenv("HOST", "127.0.0.1")
        port = int(os.getenv("PORT", "8000"))
        mcp.run(transport="sse", host=host, port=port)
    return _impl()

if __name__ == "__main__":
    main()