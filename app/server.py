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
from .llm import choose_tools_with_gpt, rewrite_snippet_with_gpt

def _parse_functions(code: str) -> List[Dict[str, Any]]:
    """Parse top-level functions in a Python snippet to extract signatures."""
    def _impl() -> List[Dict[str, Any]]:
        import ast
        import inspect
        import textwrap

        try:
            tree = ast.parse(textwrap.dedent(code))
        except SyntaxError:
            # If the snippet can't be parsed, simply report no functions instead of
            # propagating the syntax error up to the caller.
            return []
        out: List[Dict[str, Any]] = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                name = node.name
                doc = ast.get_docstring(node) or ""
                args: List[Tuple[str, str]] = []
                for a in node.args.args:
                    ann = "Any"
                    if a.annotation is not None:
                        if isinstance(a.annotation, ast.Name):
                            ann = a.annotation.id
                        else:
                            try:
                                ann = inspect.getsource(ast.fix_missing_locations(a.annotation))
                            except Exception:
                                ann = "Any"
                    args.append((a.arg, ann))
                ret = "Any"
                if node.returns is not None:
                    if isinstance(node.returns, ast.Name):
                        ret = node.returns.id
                    else:
                        try:
                            ret = inspect.getsource(ast.fix_missing_locations(node.returns))
                        except Exception:
                            ret = "Any"
                out.append({"name": name, "doc": doc, "args": args, "returns": ret})
        return out
    return _impl()


def _prepare_snippet(text: str) -> str:
    """Normalize user-submitted text to executable Python code."""

    def _impl() -> str:
        import re
        import ast
        import textwrap

        # First try to extract fenced code blocks `````python ... `````".
        fence = re.search(r"```(?:python)?\n([\s\S]*?)```", text)
        candidate = fence.group(1) if fence else text

        # If no fences are present but a ``def`` appears later in the text,
        # heuristically grab everything from the first ``def`` onward.  This
        # lets users submit prose followed by code without explicit fencing.
        if not fence and "def " in candidate:
            start = candidate.find("def ")
            candidate = candidate[start:]

        candidate = textwrap.dedent(candidate).strip()

        try:
            ast.parse(candidate)
            return candidate
        except SyntaxError:
            rewritten = rewrite_snippet_with_gpt(candidate)
            # The rewrite may include markdown fences; extract the code if present.
            fence2 = re.search(r"```(?:python)?\n([\s\S]*?)```", rewritten)
            rewritten_candidate = fence2.group(1) if fence2 else rewritten
            rewritten_candidate = textwrap.dedent(rewritten_candidate).strip()
            try:
                ast.parse(rewritten_candidate)
                return rewritten_candidate
            except Exception:
                return candidate

    return _impl()

def build_server():
    """Construct and return the FastMCP server configured with admin tools."""
    def _impl():
        from fastmcp import FastMCP
        from .registry import ensure_dirs, load_all_registered, write_tool_module, safe_mod_name, delete_tool_module

        REG_DIR = ensure_dirs("./registry")
        mcp = FastMCP("MCPForge (single port)")
        module_tool_map: Dict[str, str] = {}

        @mcp.tool(name="collector.list", description="List collected tool modules currently registered.")
        def list_collected() -> List[str]:
            return sorted(list(module_tool_map.keys()))

        @mcp.tool(name="collector.remove", description="Remove a collected tool module by module name (not tool name).")
        def remove_collected(module_name: str) -> bool:
            tool_name = module_tool_map.get(module_name)
            if tool_name:
                try:
                    mcp.remove_tool(tool_name)
                except Exception:
                    # It may have already been removed, or not exist.
                    pass
            # Now remove the module file
            ok = delete_tool_module(REG_DIR, module_name)
            if ok and module_name in module_tool_map:
                del module_tool_map[module_name]
            return ok

        @mcp.tool(name="collector.ingest_python", description="Ingest a Python snippet and expose chosen functions as tools.")
        def ingest_python(snippet_name: str, code: str) -> Dict[str, Any]:
            code = _prepare_snippet(code)
            funcs = _parse_functions(code)
            if not funcs:
                return {"created": [], "reason": "no functions found"}
            summaries = [{"name": f["name"], "doc": f["doc"], "args": f["args"]} for f in funcs]
            try:
                chosen = choose_tools_with_gpt(code, summaries)
            except Exception:
                chosen = []
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
                func_info = next((f for f in funcs if f["name"] == orig), None)
                if not func_info:
                    continue
                arg_spec = func_info["args"]
                mod_name = f"{base}_{idx}"
                write_tool_module("./registry", mod_name, code, orig, tname, desc, arg_spec)
                created.append(mod_name)
                idx += 1
            new_map = load_all_registered(mcp, "./registry")
            module_tool_map.update(new_map)
            return {"created": created}

        @mcp.tool(name="forge_health", description="Health check for the MCP Forge server.")
        def forge_health() -> str:
            import platform
            import sys
            import os
            from openai import OpenAI, AuthenticationError

            py_ver = sys.version.split()[0]
            os_name = platform.system()
            report = [f"py={py_ver}", f"os={os_name}"]
            # Check for OpenAI API key and connectivity
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                report.append("openai=no-key")
            else:
                try:
                    client = OpenAI(api_key=api_key)
                    client.models.list()
                    report.append("openai=ok")
                except AuthenticationError:
                    report.append("openai=auth-failed")
                except Exception:
                    report.append("openai=connect-failed")
            return "ok | " + " | ".join(report)

        module_tool_map.update(load_all_registered(mcp, "./registry"))

        # Expose helper functions for the web interface
        mcp.list_collected = list_collected.fn  # type: ignore[attr-defined]
        mcp.remove_collected = remove_collected.fn  # type: ignore[attr-defined]
        mcp.ingest_snippet = ingest_python.fn  # type: ignore[attr-defined]
        mcp.forge_health = forge_health.fn  # type: ignore[attr-defined]

        return mcp
    return _impl()


def build_app():
    """Create the FastAPI web application that wraps the MCP server."""

    mcp = build_server()

    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import PlainTextResponse, HTMLResponse, JSONResponse
    from fastapi.templating import Jinja2Templates
    globals()["Request"] = Request

    app = FastAPI(title="MCPForge Web UI")
    templates = Jinja2Templates(directory="app/templates")

    @app.get("/health")
    async def web_health() -> PlainTextResponse:
        return PlainTextResponse(mcp.forge_health())

    @app.get("/tools")
    async def web_list_tools() -> list[str]:
        return mcp.list_collected()

    @app.post("/tools", status_code=201)
    async def web_create_tool(request: Request) -> Response:
        if request.headers.get("content-type", "").startswith("application/json"):
            data = await request.json()
        else:
            data = await request.form()
        snippet_name = data.get("snippet_name")
        code = data.get("code")
        if not snippet_name or not code:
            raise HTTPException(400, "snippet_name and code required")
        import os
        if not os.getenv("OPENAI_API_KEY"):
            os.environ["USE_MOCK_LLM"] = "1"
        result = mcp.ingest_snippet(snippet_name, code)
        status = 201 if result.get("created") else 400
        if request.headers.get("hx-request"):
            tools = mcp.list_collected()
            headers = {"HX-Trigger": "toolAdded" if status == 201 else "toolError"}
            return templates.TemplateResponse(
                "tools.html", {"request": request, "tools": tools},
                status_code=status, headers=headers
            )
        return JSONResponse(result, status_code=status)

    @app.delete("/tools/{module}")
    async def web_remove_tool(module: str, request: Request):
        ok = mcp.remove_collected(module)
        tools = mcp.list_collected()
        if request.headers.get("hx-request"):
            headers = {"HX-Trigger": "toolRemoved" if ok else "toolError"}
            return templates.TemplateResponse(
                "tools.html", {"request": request, "tools": tools}, headers=headers
            )
        return {"removed": ok}

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        tools = mcp.list_collected()
        return templates.TemplateResponse("index.html", {"request": request, "tools": tools})

    # Mount the MCP server's SSE app under /sse
    app.mount("/sse", mcp.sse_app(path="/"))

    return app

def main(host: str | None = None, port: int | None = None):
    """Run the combined MCP and web servers on a single port."""

    def _impl():
        import os
        import uvicorn

        app = build_app()
        h = host or os.getenv("HOST", "127.0.0.1")
        p = port or int(os.getenv("PORT", "8000"))
        uvicorn.run(app, host=h, port=p)

    return _impl()

if __name__ == "__main__":
    main()
