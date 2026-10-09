"""Single catalog for existing Local-AI-Ops functions across agent adapters.

The registry wraps functions already provided by the application. It does NOT
implement GitHub, Notion, document extraction, or any other provider service.
"""
from __future__ import annotations

import inspect
import types
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Union, get_args, get_origin, get_type_hints


@dataclass(frozen=True)
class ToolSpec:
    name: str
    function: Callable[..., Any]
    description: str
    tier: str = "read"
    version: int = 1
    remote: bool = False

    def parameters(self) -> dict[str, Any]:
        signature = inspect.signature(self.function)
        annotations = get_type_hints(self.function)
        properties: dict[str, Any] = {}
        required: list[str] = []
        for name, param in signature.parameters.items():
            if param.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                  inspect.Parameter.KEYWORD_ONLY):
                raise TypeError(f"Unsupported parameter: {name}")
            prop = _schema(annotations[name])
            if param.default is inspect.Parameter.empty:
                required.append(name)
            else:
                prop["default"] = param.default
            properties[name] = prop
        return {"type": "object", "properties": properties,
                "required": required, "additionalProperties": False}

    def openai(self, chat_completions: bool = False) -> dict[str, Any]:
        entry = {"name": self.name, "description": self.description,
                 "parameters": self.parameters()}
        return ({"type": "function", "function": entry} if chat_completions
                else {"type": "function", **entry})

    def anthropic(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description,
                "input_schema": self.parameters()}


_TOOLS: dict[str, ToolSpec] = {}
_TIERS = {"read", "write", "llm", "admin"}


def tool(*, name: str, tier: str = "read", version: int = 1,
         remote: bool = False) -> Callable:
    """Declare an existing Python operation once for all supported agents."""
    if not name.isidentifier() or tier not in _TIERS or version < 1:
        raise ValueError("Invalid name, tier, or version")

    def register(fn: Callable) -> Callable:
        if name in _TOOLS:
            raise ValueError(f"Duplicate tool: {name}")
        spec = ToolSpec(name=name, function=fn,
                        description=inspect.getdoc(fn) or name,
                        tier=tier, version=version, remote=remote)
        spec.parameters()  # fail early for unsupported signatures
        _TOOLS[name] = spec
        return fn

    return register


def _schema(annotation: Any) -> dict[str, Any]:
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        return {"anyOf": [_schema(item) for item in get_args(annotation)]}
    if annotation is type(None):
        return {"type": "null"}
    if origin is list:
        args = get_args(annotation)
        return {"type": "array", "items": _schema(args[0] if args else str)}
    if origin is dict or annotation is dict:
        return {"type": "object", "additionalProperties": True}
    for cls, kind in ((str, "string"), (bool, "boolean"), (int, "integer"),
                      (float, "number")):
        if annotation is cls:
            return {"type": kind}
    raise TypeError(f"Unsupported argument type: {annotation!r}")


def _valid(value: Any, annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        return any(_valid(value, item) for item in get_args(annotation))
    if annotation is type(None):
        return value is None
    if origin is list:
        args = get_args(annotation)
        return isinstance(value, list) and all(
            _valid(item, args[0]) for item in value) if args else isinstance(value, list)
    if origin is dict or annotation is dict:
        return isinstance(value, dict) and all(isinstance(key, str) for key in value)
    if annotation is int:
        return type(value) is int
    if annotation is float:
        return type(value) in (float, int)
    return type(value) is annotation


def list_tools(*, remote: bool | None = None) -> list[ToolSpec]:
    import_module("aiops.tool_catalog")
    tools = _TOOLS.values()
    if remote is not None:
        tools = (entry for entry in tools if entry.remote is remote)
    return sorted(tools, key=lambda item: item.name)


def get_tool(name: str) -> ToolSpec:
    import_module("aiops.tool_catalog")
    try:
        return _TOOLS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown tool: {name}") from exc


def dispatch(name: str, arguments: dict[str, Any], *, remote: bool = False) -> Any:
    """Validate arguments before invoking an allowlisted tool.

    For a future HTTP adapter, remote=True rejects all tools not explicitly
    opted into remote execution. Never expose the stdio catalog wholesale.
    """
    spec = get_tool(name)
    if remote and not spec.remote:
        raise PermissionError(f"Tool is not available remotely: {name}")
    if not isinstance(arguments, dict):
        raise TypeError("Tool arguments must be a JSON object")
    signature = inspect.signature(spec.function)
    bound = signature.bind(**arguments)
    annotations = get_type_hints(spec.function)
    for field, value in bound.arguments.items():
        if not _valid(value, annotations[field]):
            raise TypeError(f"Invalid argument type: {field}")
    return spec.function(**bound.arguments)
