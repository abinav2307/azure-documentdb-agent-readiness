"""Everything one pipeline run shares between stages."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .config import Settings
from .decision_log import DecisionLog
from .tools.environment import SkillInfo
from .tools.mcp_inventory import McpServerConfig, McpServerStatus


@dataclass
class RunContext:
    settings: Settings
    run_dir: Path
    sample_name: str
    sample_prompt: str
    skill_md: str
    log: DecisionLog
    client_factory: Callable[[int | None], Any]  # max LLM round-trips -> chat client
    skills: list[SkillInfo] = field(default_factory=list)
    skill_roots: list[Path] = field(default_factory=list)
    mcp_configs: list[McpServerConfig] = field(default_factory=list)
    mcp_statuses: list[McpServerStatus] = field(default_factory=list)
    requirements: str = ""  # reference requirements: shown to the reviewer and auditor, never to the builder

    @property
    def app_dir(self) -> Path:
        return self.run_dir / "app"

    def requirements_block(self) -> str:
        if not self.requirements.strip():
            return "<reference_requirements>No reference requirements file was supplied for this run.</reference_requirements>"
        return f"<reference_requirements>\n{self.requirements.strip()}\n</reference_requirements>"

    def sample_block(self) -> str:
        """The sample prompt and shared skill.md, formatted for an agent message."""
        parts = [f"<sample_prompt name=\"{self.sample_name}\">\n{self.sample_prompt.strip()}\n</sample_prompt>"]
        if self.skill_md.strip():
            parts.append(f"<skill_md>\n{self.skill_md.strip()}\n</skill_md>")
        else:
            parts.append("<skill_md>No shared skill.md was supplied for this run.</skill_md>")
        return "\n\n".join(parts)
