"""MCP servers: read mcp.json, check which ones really answer, build tools.

A server listed in mcp.json but failing to start is the common case that
silently degrades a build, so stage 2 connects to each one and lists its
tools rather than trusting configuration. Only servers that answered are
handed to later agents.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_framework import MCPStdioTool, MCPStreamableHTTPTool

_VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass
class McpServerConfig:
    name: str
    purpose: str
    required: bool
    stages: list[str]
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    allowed_tools: list[str] = field(default_factory=list)
    missing_variables: list[str] = field(default_factory=list)
    documentation: bool = False  # a public documentation search server


@dataclass
class McpServerStatus:
    name: str
    purpose: str
    required: bool
    stages: list[str]
    available: bool
    detail: str
    tools: list[dict[str, str]]
    documentation: bool = False


def load_mcp_config(path: Path) -> list[McpServerConfig]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    servers = []
    for name, spec in (raw.get("servers") or {}).items():
        if spec.get("disabled"):
            continue
        missing: list[str] = []
        servers.append(
            McpServerConfig(
                name=name,
                purpose=spec.get("purpose", ""),
                required=bool(spec.get("required", False)),
                stages=list(spec.get("stages", ["readiness", "build", "audit"])),
                command=_expand(spec.get("command", ""), missing),
                args=[_expand(a, missing) for a in spec.get("args", [])],
                env={k: _expand(v, missing) for k, v in (spec.get("env") or {}).items()},
                url=_expand(spec.get("url", ""), missing),
                headers={k: _expand(v, missing) for k, v in (spec.get("headers") or {}).items()},
                allowed_tools=list(spec.get("allowed_tools", [])),
                documentation=bool(spec.get("documentation", False)),
                missing_variables=sorted(set(missing)),
            )
        )
    return servers


def _expand(value: str, missing: list[str]) -> str:
    def replace(match: re.Match) -> str:
        found = os.environ.get(match.group(1))
        if found is None:
            missing.append(match.group(1))
            return ""
        return found

    return _VAR.sub(replace, value)


def make_tool(config: McpServerConfig) -> Any:
    """Create an (unconnected) Agent Framework MCP tool for one server."""
    common: dict[str, Any] = {
        "name": config.name,
        # Prefix tool names with the server name ("azure_cosmos"), so two
        # servers cannot collide and the trace shows where a call went.
        "tool_name_prefix": config.name,
        "description": config.purpose or None,
        "approval_mode": "never_require",
        "allowed_tools": config.allowed_tools or None,
        "load_prompts": False,
        "request_timeout": 120,
    }
    if config.url:
        return MCPStreamableHTTPTool(url=config.url, static_headers=config.headers or None, **common)
    # Resolve to a full path so that npx.cmd and friends start on Windows.
    command = shutil.which(config.command) or config.command
    return MCPStdioTool(command=command, args=config.args, env={**os.environ, **config.env}, **common)


async def probe_server(config: McpServerConfig, timeout_seconds: int = 90) -> McpServerStatus:
    """Start the server, list its tools, shut it down."""

    def status(available: bool, detail: str, tools: list[dict[str, str]] | None = None) -> McpServerStatus:
        return McpServerStatus(
            config.name, config.purpose, config.required, config.stages, available, detail, tools or [], config.documentation
        )

    if config.missing_variables:
        return status(False, "environment variables not set: " + ", ".join(config.missing_variables))
    if not config.url and not config.command:
        return status(False, "mcp.json entry has neither 'command' nor 'url'")

    async def connect_and_list() -> list[dict[str, str]]:
        async with make_tool(config) as server:
            return [
                {"name": f.name, "description": " ".join((f.description or "").split())[:200]}
                for f in server.functions
            ]

    try:
        tools = await asyncio.wait_for(connect_and_list(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        return status(False, f"no answer within {timeout_seconds}s")
    except BaseException as exc:  # MCP start-up failures arrive as exception groups
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return status(False, _describe(exc))
    return status(True, f"{len(tools)} tools", tools)


async def probe_all(configs: list[McpServerConfig]) -> list[McpServerStatus]:
    # One at a time: several npx cold starts in parallel are slow and noisy.
    return [await probe_server(c) for c in configs]


def tools_for_stage(configs: list[McpServerConfig], statuses: list[McpServerStatus], stage: str) -> list[Any]:
    available = {s.name for s in statuses if s.available}
    return [make_tool(c) for c in configs if c.name in available and stage in c.stages]


def _describe(exc: BaseException) -> str:
    inner = getattr(exc, "exceptions", None)
    if inner:
        return "; ".join(_describe(e) for e in inner)[:400]
    message = exc.args[0] if exc.args and isinstance(exc.args[0], str) else str(exc)
    return " ".join(message.split())[:400]
