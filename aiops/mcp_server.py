"""Expose existing Local-AI-Ops operations via the shared registry and MCP stdio."""
from __future__ import annotations

from aiops.registry import list_tools


def build():
    try:  # preserve the existing MCP 2.x compatibility path
        from mcp.server.mcpserver import MCPServer as Server
    except ImportError:  # MCP 1.x FastMCP
        from mcp.server.fastmcp import FastMCP as Server

    server = Server("aiops")
    for spec in list_tools():
        server.tool()(spec.function)  # existing names/signatures are unchanged
    return server


def run() -> None:
    build().run()
