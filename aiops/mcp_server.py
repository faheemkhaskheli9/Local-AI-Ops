"""Expose the shared registry over MCP stdio; every call goes through `bind`/`dispatch`."""
from __future__ import annotations

import functools
import inspect
import json
from typing import Any, get_type_hints

from aiops.registry import ToolSpec, bind, dispatch, get_tool, list_tools


def _sdk():
    try:  # MCP 2.x
        from mcp.server.mcpserver import MCPServer as Server
        from mcp.server.mcpserver.exceptions import ToolError
    except ImportError:  # MCP 1.x FastMCP
        from mcp.server.fastmcp import FastMCP as Server
        from mcp.server.fastmcp.exceptions import ToolError
    return Server, ToolError


def _pre_parse(spec: ToolSpec, arguments: dict[str, Any]) -> dict[str, Any]:
    """Accept lists/objects sent as JSON strings, as the MCP SDK does for its clients."""
    hints = get_type_hints(spec.function)
    out = dict(arguments)
    for key, value in arguments.items():
        if isinstance(value, str) and hints.get(key, str) is not str:
            try:
                parsed = json.loads(value)
            except (ValueError, RecursionError):
                continue
            if not isinstance(parsed, (str, int, float)):
                out[key] = parsed
    return out


def _wrapper(spec: ToolSpec):
    """Same name, signature and docstring as the tool; the body calls `dispatch`."""
    hints = get_type_hints(spec.function)
    signature = inspect.signature(spec.function)
    params = [p.replace(annotation=hints[p.name]) for p in signature.parameters.values()]

    @functools.wraps(spec.function)
    def call(**arguments):
        return dispatch(spec.name, arguments)

    call.__signature__ = signature.replace(parameters=params,
                                           return_annotation=hints.get("return", Any))
    call.__annotations__ = hints
    call.__doc__ = spec.description
    del call.__wrapped__  # keep the SDK on the replaced signature
    return call


def build():
    Server, ToolError = _sdk()

    class _Server(Server):
        async def call_tool(self, name, arguments, *args, **kwargs):
            # Check the raw request with the registry's strict rules before the SDK
            # coerces anything, so MCP rejects exactly what `dispatch` rejects.
            try:
                if isinstance(arguments, dict):
                    arguments = _pre_parse(get_tool(name), arguments)
                bind(name, arguments)
            except (TypeError, ValueError, PermissionError) as exc:
                raise ToolError(str(exc)) from exc
            return await super().call_tool(name, arguments, *args, **kwargs)

    server = _Server("aiops")
    for spec in list_tools():
        server.tool(name=spec.name, description=spec.description)(_wrapper(spec))
        # Advertise the registry schema, identical to the OpenAI/Anthropic exports.
        server._tool_manager.get_tool(spec.name).parameters = spec.parameters()
    return server


def run() -> None:
    build().run()
