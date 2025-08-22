"""
Utilities for interacting with OpenAI's responses API to curate tools.

The functions in this module defer all imports until inside functions
to respect the user's preference that imports live inside function bodies.
"""

from __future__ import annotations
from typing import List, Dict, Any

def choose_tools_with_gpt(code: str, fn_summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ask OpenAI gpt-4.1-nano to select functions from ``fn_summaries`` to expose
    as MCP tools and to provide concise names and descriptions.

    Parameters
    ----------
    code:
        The raw Python snippet containing candidate functions.
    fn_summaries:
        A list of dictionaries describing functions present in the snippet.  Each
        dictionary should include at least ``name`` (original function name),
        ``doc`` (docstring or empty string), and ``args`` (list of argument name/type tuples).

    Returns
    -------
    List[Dict[str, Any]]:
        A list of dictionaries for each selected tool with keys:
        ``original_name`` – the original function name in the snippet;
        ``tool_name`` – a kebab or snake-cased name to use for the MCP tool;
        ``description`` – a concise description (<= 120 characters).

    Notes
    -----
    The OpenAI API key must be provided via the ``OPENAI_API_KEY`` environment
    variable.  This function will return an empty list if no valid response
    can be parsed.
    """
    def _call_openai() -> List[Dict[str, Any]]:
        # Deferred import: only import when the function is called.
        from openai import OpenAI
        import os
        import json
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Compose a concise system prompt instructing the model to return JSON.
        system = (
            "You are a careful code curator. Given candidate Python functions, "
            "pick only safe, side‑effect‑light functions to expose as MCP tools. "
            "Return strict JSON: an array of objects with fields "
            "`original_name`, `tool_name` (kebab or snake case), and `description` (<=120 chars). "
            "Prefer tiny, deterministic tools. If nothing is safe/useful, return []."
        )
        user = {
            "code": code,
            "functions": fn_summaries,
        }
        rsp = client.responses.create(
            model="gpt-4.1-nano",
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": [
                    {"type": "input_text", "text": json.dumps(user)}
                ]}
            ],
            text={"format": "json_object"}
        )
        text = rsp.output_text
        try:
            obj = json.loads(text)
        except Exception:
            return []
        # Accept two possible response shapes: top-level list or {"tools": [...]}
        if isinstance(obj, dict) and "tools" in obj and isinstance(obj["tools"], list):
            return obj["tools"]
        if isinstance(obj, list):
            return obj
        return []

    return _call_openai()