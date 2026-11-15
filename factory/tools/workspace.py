"""File tools confined to one root folder."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from agent_framework import tool
from pydantic import Field

MAX_READ_CHARS = 60_000
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "bin", "obj", ".pytest_cache"}


class Workspace:
    """Read (and optionally write) files under `root`. Paths that escape are refused."""

    def __init__(self, root: Path, writable: bool) -> None:
        self.root = root.resolve()
        self.writable = writable
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError(f"'{relative_path}' is outside the workspace. Use a path relative to the workspace root.")
        return candidate

    # -- plain methods (also used directly by tests) -------------------------

    def list_files(self, folder: str = ".") -> str:
        base = self.resolve(folder)
        if not base.exists():
            return f"'{folder}' does not exist."
        rows: list[str] = []
        for path in sorted(base.rglob("*")):
            if any(part in SKIP_DIRS for part in path.relative_to(self.root).parts):
                continue
            if path.is_file():
                rows.append(f"{path.relative_to(self.root).as_posix()}  ({path.stat().st_size} bytes)")
            if len(rows) >= 500:
                rows.append("... listing truncated at 500 files")
                break
        return "\n".join(rows) or "(empty)"

    def read_file(self, path: str, start_line: int = 1, max_lines: int = 400) -> str:
        target = self.resolve(path)
        if not target.is_file():
            return f"'{path}' is not a file."
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(start_line, 1)
        chunk = lines[start - 1 : start - 1 + max_lines]
        numbered = "\n".join(f"{start + i:>5}  {line}" for i, line in enumerate(chunk))
        if len(numbered) > MAX_READ_CHARS:
            numbered = numbered[:MAX_READ_CHARS] + "\n... truncated"
        tail = "" if start - 1 + max_lines >= len(lines) else f"\n... {len(lines) - (start - 1 + max_lines)} more lines"
        return numbered + tail

    def write_file(self, path: str, content: str) -> str:
        target = self.resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8", newline="\n")
        return f"{'Overwrote' if existed else 'Created'} {target.relative_to(self.root).as_posix()} ({len(content)} chars)."

    def search_text(self, text: str, folder: str = ".") -> str:
        base = self.resolve(folder)
        needle = text.lower()
        hits: list[str] = []
        for path in sorted(base.rglob("*")):
            if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(self.root).parts):
                continue
            try:
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if needle in line.lower():
                        hits.append(f"{path.relative_to(self.root).as_posix()}:{number}: {line.strip()[:200]}")
                        if len(hits) >= 100:
                            return "\n".join(hits) + "\n... truncated at 100 matches"
            except (UnicodeDecodeError, OSError):
                continue
        return "\n".join(hits) or "No matches."

    # -- agent tools ---------------------------------------------------------

    def tools(self) -> list:
        ws = self

        @tool(name="list_files", approval_mode="never_require")
        def list_files(folder: Annotated[str, Field(description="Folder relative to the workspace root. '.' for everything.")]) -> str:
            """List files in the workspace, recursively, with sizes."""
            return _safe(lambda: ws.list_files(folder))

        @tool(name="read_file", approval_mode="never_require")
        def read_file(
            path: Annotated[str, Field(description="File path relative to the workspace root.")],
            start_line: Annotated[int, Field(description="First line to return, starting at 1.")],
            max_lines: Annotated[int, Field(description="How many lines to return. 400 is a good default.")],
        ) -> str:
            """Read a text file with line numbers."""
            return _safe(lambda: ws.read_file(path, start_line, max_lines))

        @tool(name="search_text", approval_mode="never_require")
        def search_text(
            text: Annotated[str, Field(description="Case-insensitive text to look for.")],
            folder: Annotated[str, Field(description="Folder to search, relative to the workspace root.")],
        ) -> str:
            """Find lines containing some text. Returns file:line: text."""
            return _safe(lambda: ws.search_text(text, folder))

        tools = [list_files, read_file, search_text]

        if self.writable:

            @tool(name="write_file", approval_mode="never_require")
            def write_file(
                path: Annotated[str, Field(description="File path relative to the workspace root. Folders are created.")],
                content: Annotated[str, Field(description="The complete file content.")],
            ) -> str:
                """Create or overwrite a text file."""
                return _safe(lambda: ws.write_file(path, content))

            tools.append(write_file)
        return tools


def _safe(action) -> str:
    try:
        return action()
    except (ValueError, OSError) as exc:
        return f"ERROR: {exc}"
