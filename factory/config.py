"""Settings, read from environment variables (and .env if present)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_DIR / "prompts"

# Executables the builder may run. `az` and `azd` are handled separately:
# read-only by default, see tools/shell.py.
DEFAULT_ALLOWED_COMMANDS = (
    "python,python3,py,pip,pip3,pytest,uv,node,npm,npx,dotnet,git,az,azd,docker,mongosh,terraform,bicep"
)


def _split(value: str) -> list[str]:
    return [v.strip() for v in value.replace(";", ",").split(",") if v.strip()]


@dataclass
class Settings:
    provider: str = "azure_openai"          # azure_openai | openai | foundry
    model: str = ""                         # deployment or model name
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""          # empty -> use `az login` credentials
    foundry_project_endpoint: str = ""
    openai_api_key: str = ""
    openai_base_url: str = ""               # empty -> api.openai.com; set for a private or compatible endpoint
    openai_api_style: str = "responses"     # responses | chat_completions

    skill_paths: list[Path] = field(default_factory=list)
    mcp_config: Path = PROJECT_DIR / "mcp.json"
    checklist: Path = PROJECT_DIR / "best-practices" / "checklist.md"
    runs_dir: Path = PROJECT_DIR / "runs"

    allowed_commands: list[str] = field(default_factory=list)
    allow_azure_writes: bool = False
    command_timeout_seconds: int = 600
    builder_max_iterations: int = 150
    request_timeout_seconds: int = 1800     # one model call; large structured answers can take many minutes
    request_retries: int = 2
    max_prior_beliefs: int = 25             # prior beliefs carried into practice discovery
    max_iterations: int = 40

    @classmethod
    def load(cls, env_file: Path | None = None) -> "Settings":
        load_dotenv(env_file or PROJECT_DIR / ".env")
        # A line such as `OPENAI_BASE_URL=` puts an EMPTY variable in the environment. The OpenAI
        # and Azure SDKs read these variables themselves and treat empty as a real value (an empty
        # base address, for example), so blank settings are removed and count as not set.
        for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "OPENAI_ORG_ID", "AZURE_OPENAI_ENDPOINT",
                     "AZURE_OPENAI_API_KEY", "FOUNDRY_PROJECT_ENDPOINT", "DOCUMENTDB_URI"):
            if name in os.environ and not os.environ[name].strip():
                del os.environ[name]
        env = os.environ.get
        # `npx skills add Azure/documentdb-agent-kit`, run from this folder,
        # installs into .agents/skills. Home-folder skill directories are left
        # out by default so unrelated skills do not distract the agents.
        default_skill_paths = [
            PROJECT_DIR / ".agents" / "skills",
            PROJECT_DIR / "skills",
        ]
        configured = [Path(p).expanduser() for p in _split(env("FACTORY_SKILL_PATHS", ""))]
        return cls(
            provider=env("FACTORY_PROVIDER", "azure_openai").lower(),
            model=env("FACTORY_MODEL", ""),
            azure_openai_endpoint=env("AZURE_OPENAI_ENDPOINT", ""),
            azure_openai_api_key=env("AZURE_OPENAI_API_KEY", ""),
            foundry_project_endpoint=env("FOUNDRY_PROJECT_ENDPOINT", ""),
            openai_api_key=env("OPENAI_API_KEY", ""),
            openai_base_url=env("OPENAI_BASE_URL", "").strip(),
            openai_api_style=env("OPENAI_API_STYLE", "responses").strip().lower(),
            skill_paths=configured or default_skill_paths,
            mcp_config=Path(env("FACTORY_MCP_CONFIG", str(PROJECT_DIR / "mcp.json"))),
            checklist=Path(env("FACTORY_CHECKLIST", str(PROJECT_DIR / "best-practices" / "checklist.md"))),
            runs_dir=Path(env("FACTORY_RUNS_DIR", str(PROJECT_DIR / "runs"))),
            allowed_commands=_split(env("FACTORY_ALLOWED_COMMANDS", DEFAULT_ALLOWED_COMMANDS)),
            allow_azure_writes=env("FACTORY_ALLOW_AZURE_WRITES", "false").lower() in ("1", "true", "yes"),
            command_timeout_seconds=int(env("FACTORY_COMMAND_TIMEOUT", "600")),
            builder_max_iterations=int(env("FACTORY_BUILDER_MAX_ITERATIONS", "150")),
            request_timeout_seconds=int(env("FACTORY_REQUEST_TIMEOUT", "1800")),
            request_retries=int(env("FACTORY_REQUEST_RETRIES", "2")),
            max_prior_beliefs=int(env("FACTORY_MAX_PRIOR_BELIEFS", "25")),
            max_iterations=int(env("FACTORY_MAX_ITERATIONS", "40")),
        )


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")
