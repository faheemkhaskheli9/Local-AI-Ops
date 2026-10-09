"""Export existing tool schemas for OpenAI and Anthropic function calling.

Run: python -m aiops.export openai|openai-chat|anthropic
"""
from __future__ import annotations

import argparse
import json

from aiops.registry import list_tools


def export(format: str) -> list[dict]:
    tools = list_tools()
    if format == "openai":
        return [tool.openai() for tool in tools]
    if format == "openai-chat":
        return [tool.openai(chat_completions=True) for tool in tools]
    if format == "anthropic":
        return [tool.anthropic() for tool in tools]
    raise ValueError("Supported formats: openai, openai-chat, anthropic")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("format", choices=["openai", "openai-chat", "anthropic"])
    args = parser.parse_args(argv)
    print(json.dumps(export(args.format), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
