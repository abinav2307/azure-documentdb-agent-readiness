"""A command runner for the builder, with a policy in front of it.

* Only allow-listed executables run.
* No shell: one program per call, so no pipes, redirects or chaining.
* The working directory stays inside the app folder.
* `az` / `azd` are read-only unless Azure writes were switched on for the run.
  A refused command tells the agent to log the decision and fall back to
  writing infrastructure files instead of provisioning.
"""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Annotated

from agent_framework import tool
from pydantic import Field

from .workspace import Workspace

MAX_OUTPUT_CHARS = 12_000

# `az` verbs that only read. Anything else counts as a write.
AZ_READ_VERBS = {
    "list", "show", "version", "find", "help",
    "list-locations", "list-skus", "list-connection-strings", "check-name-availability", "what-if", "validate", "export",
}
# `azd init`, `env` and `config` only touch local files.
AZD_READ_VERBS = {"version", "init", "env", "config", "show", "template"}


class CommandPolicy:
    def __init__(self, allowed: list[str], allow_azure_writes: bool) -> None:
        self.allowed = {a.lower() for a in allowed}
        self.allow_azure_writes = allow_azure_writes

    def check(self, argv: list[str]) -> str | None:
        """Return a refusal message, or None if the command may run."""
        if not argv:
            return "Empty command."
        exe = Path(argv[0]).name.lower()
        for suffix in (".exe", ".cmd", ".bat"):
            exe = exe.removesuffix(suffix)
        if exe not in self.allowed:
            return (
                f"REFUSED: '{exe}' is not on the allowed command list ({', '.join(sorted(self.allowed))}). "
                "Log this with log_decision (reason_source=tool_unavailable) and choose another route."
            )
        if exe in ("az", "azd") and not self.allow_azure_writes:
            read_verbs = AZ_READ_VERBS if exe == "az" else AZD_READ_VERBS
            # Command words are the positionals before the first flag, so a
            # flag *value* such as `--name list` cannot pass as a read verb.
            words: list[str] = []
            for arg in argv[1:]:
                if arg.startswith("-"):
                    break
                words.append(arg.lower())
            asks_for_help = any(a in ("--help", "-h", "--version") for a in argv[1:])
            if not asks_for_help and not any(w in read_verbs for w in words):
                return (
                    f"REFUSED: this run may not change Azure resources, and '{' '.join(argv[:4])} ...' is not a read-only command. "
                    "Write the infrastructure as files (Bicep, Terraform or a CLI script) in the app instead, "
                    "and record that with log_decision (reason_source=tool_unavailable)."
                )
        return None


def split_command(command: str) -> list[str]:
    argv = shlex.split(command, posix=(os.name != "nt"))
    if os.name == "nt":
        argv = [a[1:-1] if len(a) >= 2 and a[0] == a[-1] and a[0] in "\"'" else a for a in argv]
    return argv


def run_command_tool(workspace: Workspace, policy: CommandPolicy, timeout_seconds: int):
    @tool(name="run_command", approval_mode="never_require")
    def run_command(
        command: Annotated[
            str,
            Field(description="One program with its arguments, e.g. 'python -m pytest -q'. No pipes, redirects, '&&' or ';'."),
        ],
        working_folder: Annotated[str, Field(description="Folder to run in, relative to the workspace root. '.' for the root.")],
    ) -> str:
        """Run one command inside the app workspace and return its exit code and output."""
        try:
            argv = split_command(command)
            cwd = workspace.resolve(working_folder)
        except ValueError as exc:
            return f"ERROR: {exc}"
        if any(token in ("|", "&&", "||", ";", ">", ">>", "<") for token in argv):
            return "REFUSED: run one program per call. Pipes, redirects and chaining are not available."
        refusal = policy.check(argv)
        if refusal:
            return refusal
        resolved = shutil.which(argv[0])
        if not resolved:
            return (
                f"NOT INSTALLED: '{argv[0]}' was not found on PATH. "
                "Log this with log_decision (reason_source=tool_unavailable) and choose another route."
            )
        try:
            done = subprocess.run(
                [resolved, *argv[1:]],
                cwd=cwd,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=timeout_seconds,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            return f"TIMEOUT after {timeout_seconds}s. Long-running servers cannot be started with this tool."
        except OSError as exc:
            return f"ERROR: {exc}"
        output = (done.stdout or "") + (("\n[stderr]\n" + done.stderr) if done.stderr else "")
        if len(output) > MAX_OUTPUT_CHARS:
            half = MAX_OUTPUT_CHARS // 2
            output = output[:half] + "\n... output truncated ...\n" + output[-half:]
        return f"exit code {done.returncode}\n{output.strip()}"

    return run_command
