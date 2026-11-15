"""Stage 4: the audit trail.

This is deliberately not an agent. Decisions are appended by whichever agent
is making them, at the moment it makes them, through the `log_decision` tool.
A log reconstructed afterwards would be a rationalization of the result.

Two files sit side by side in the run folder:

* decisions.jsonl - what the agents say they decided and why.
* events.jsonl    - every tool call that actually happened (written by
                    middleware, so agents cannot edit or omit entries).

The auditor reads both, which lets it check stated reasons against what ran.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, get_args

from agent_framework import FunctionInvocationContext, function_middleware, tool
from pydantic import Field

from .models import Decision, ReasonSource


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DecisionLog:
    def __init__(self, run_dir: Path) -> None:
        self.path = run_dir / "decisions.jsonl"
        self.events_path = run_dir / "events.jsonl"
        self.markdown_path = run_dir / "04-decisions.md"

    # -- decisions ---------------------------------------------------------

    def read(self) -> list[Decision]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return [Decision.model_validate_json(line) for line in lines if line.strip()]

    def add(
        self,
        stage: str,
        decision: str,
        reason: str,
        reason_source: str,
        alternatives: list[str] | None = None,
        evidence: str = "",
    ) -> Decision:
        if reason_source not in get_args(ReasonSource):
            raise ValueError(f"reason_source must be one of {', '.join(get_args(ReasonSource))}")
        entry = Decision(
            id=f"D{len(self.read()) + 1:03d}",
            timestamp=_now(),
            stage=stage,
            decision=decision.strip(),
            alternatives=[a.strip() for a in (alternatives or []) if a.strip()],
            reason=reason.strip(),
            reason_source=reason_source,  # type: ignore[arg-type]
            evidence=evidence.strip(),
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")
        return entry

    def tool_for(self, stage: str):
        """The `log_decision` tool, bound to one stage."""
        log = self

        @tool(name="log_decision", approval_mode="never_require")
        def log_decision(
            decision: Annotated[str, Field(description="What you chose, in one sentence. Start with 'I chose' or 'I used'.")],
            alternatives: Annotated[list[str], Field(description="The options you rejected. Empty only if there was truly one option.")],
            reason: Annotated[str, Field(description="Why this option over the alternatives.")],
            reason_source: Annotated[
                ReasonSource,
                Field(description="Where the reason came from. Use model_default when no prompt, skill, doc or tool result told you."),
            ],
            evidence: Annotated[str, Field(description="Quote from the prompt, skill name, doc URL, or the error message that forced the choice.")],
        ) -> str:
            """Record a decision in the audit trail BEFORE acting on it.

            Call this whenever you pick between alternatives: language, driver and
            version, auth mode, CLI vs ARM vs MCP, index type, data model, SDK,
            deployment method, or any workaround for a missing tool.
            """
            entry = log.add(stage, decision, reason, reason_source, alternatives, evidence)
            return f"Recorded as {entry.id}."

        return log_decision

    # -- tool-call trace ----------------------------------------------------

    def trace_middleware(self, stage: str):
        """Function middleware that records every tool call to events.jsonl."""
        events_path = self.events_path

        @function_middleware
        async def trace(context: FunctionInvocationContext, call_next) -> None:
            started = time.monotonic()
            event: dict[str, Any] = {
                "timestamp": _now(),
                "stage": stage,
                "tool": context.function.name,
                "arguments": _clip(_as_plain(context.arguments), 1500),
            }
            try:
                await call_next()
                text = _result_text(context.result)
                first_word = text.split(":", 1)[0].split(" ", 1)[0]
                event["outcome"] = {
                    "REFUSED": "refused", "ERROR": "error", "NOT": "not_installed", "TIMEOUT": "timeout",
                }.get(first_word, "ok")
                event["result"] = _clip(text, 600)
            except Exception as exc:  # recorded, then re-raised to the loop
                event["outcome"] = "exception"
                event["result"] = _clip(f"{type(exc).__name__}: {exc}", 600)
                raise
            finally:
                event["seconds"] = round(time.monotonic() - started, 2)
                with events_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")

        return trace

    # -- rendering ----------------------------------------------------------

    def render_markdown(self) -> str:
        decisions = self.read()
        out = ["# Decision log", ""]
        if not decisions:
            out.append("No decisions were recorded.")
        counts: dict[str, int] = {}
        for d in decisions:
            counts[d.reason_source] = counts.get(d.reason_source, 0) + 1
        if counts:
            out.append("| Reason came from | Decisions |")
            out.append("|---|---|")
            out += [f"| {k} | {v} |" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]
            out.append("")
            out.append(
                "`model_default` means the agent had no prompt, skill, doc or tool result to go on. "
                "Each one is a candidate prompt or documentation gap."
            )
            out.append("")
        for d in decisions:
            out.append(f"## {d.id} ({d.stage}): {d.decision}")
            out.append("")
            if d.alternatives:
                out.append("- **Instead of:** " + "; ".join(d.alternatives))
            out.append(f"- **Because:** {d.reason}")
            out.append(f"- **Reason came from:** `{d.reason_source}`")
            if d.evidence:
                out.append(f"- **Evidence:** {d.evidence}")
            out.append(f"- **When:** {d.timestamp}")
            out.append("")
        text = "\n".join(out)
        self.markdown_path.write_text(text, encoding="utf-8")
        return text


def _result_text(result: Any) -> str:
    """Tool results arrive as a string or as a list of framework Content items."""
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    if isinstance(result, (list, tuple)):
        return "\n".join(_result_text(item) for item in result)
    text = getattr(result, "text", None)
    return text if isinstance(text, str) else str(result)


def _as_plain(arguments: Any) -> Any:
    if hasattr(arguments, "model_dump"):
        return arguments.model_dump()
    try:
        return dict(arguments)
    except Exception:
        return str(arguments)


def _clip(value: Any, limit: int) -> Any:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    return text if len(text) <= limit else text[:limit] + f"... [{len(text) - limit} more chars]"
