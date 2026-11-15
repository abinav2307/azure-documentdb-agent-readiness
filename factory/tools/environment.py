"""Deterministic inventory of what is on this machine: CLIs, skills, sign-in.

No model is involved here. Stage 2 hands these facts to the readiness agent
so its verdict rests on what was observed, not on what it assumes.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

# name -> (version arguments, what it is for)
CLI_PROBES: dict[str, tuple[list[str], str]] = {
    "az": (["version", "--output", "json"], "Provision and inspect Azure resources"),
    "azd": (["version"], "Template-based provision and deploy"),
    "bicep": (["--version"], "Infrastructure as code"),
    "terraform": (["version"], "Infrastructure as code"),
    "node": (["--version"], "Run npx-based MCP servers; Node.js samples"),
    "npx": (["--version"], "Start MCP servers and install agent skills"),
    "python": (["--version"], "Python samples"),
    "dotnet": (["--version"], ".NET samples"),
    "docker": (["--version"], "Run DocumentDB locally for tests"),
    "mongosh": (["--version"], "Check connectivity and indexes by hand"),
    "git": (["--version"], "Source control"),
}


@dataclass
class CliStatus:
    name: str
    purpose: str
    available: bool
    detail: str


@dataclass
class SkillInfo:
    name: str
    description: str
    path: str


def probe_clis() -> list[CliStatus]:
    results = []
    for name, (args, purpose) in CLI_PROBES.items():
        exe = shutil.which(name)
        if not exe:
            results.append(CliStatus(name, purpose, False, "not found on PATH"))
            continue
        try:
            done = subprocess.run([exe, *args], capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL)
            text = (done.stdout or done.stderr or "").strip().replace("\r", "")
            results.append(CliStatus(name, purpose, done.returncode == 0, " ".join(text.split())[:160]))
        except (subprocess.TimeoutExpired, OSError) as exc:
            results.append(CliStatus(name, purpose, False, f"{type(exc).__name__}: {exc}"))
    return results


def probe_azure_login() -> CliStatus:
    purpose = "Signed-in Azure identity for provisioning and Entra auth"
    exe = shutil.which("az")
    if not exe:
        return CliStatus("az login", purpose, False, "Azure CLI not installed")
    try:
        done = subprocess.run(
            [exe, "account", "show", "--query", "{subscription:name, tenant:tenantId}", "--output", "json"],
            capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return CliStatus("az login", purpose, False, f"{type(exc).__name__}: {exc}")
    if done.returncode != 0:
        return CliStatus("az login", purpose, False, "not signed in (run `az login`)")
    return CliStatus("az login", purpose, True, " ".join(done.stdout.split())[:160])


def find_skills(skill_paths: list[Path]) -> list[SkillInfo]:
    """Find installed agent skills (folders that contain a SKILL.md)."""
    found: dict[str, SkillInfo] = {}
    for root in skill_paths:
        if not root.is_dir():
            continue
        for skill_file in sorted(root.glob("**/SKILL.md")):
            if len(skill_file.relative_to(root).parts) > 4:
                continue
            name, description = _read_frontmatter(skill_file)
            found.setdefault(name, SkillInfo(name, description, str(skill_file.parent)))
    return list(found.values())


def skill_public_urls(skill_paths: list[Path]) -> dict[str, str]:
    """Public address of each installed skill, from the skills installer's lock file.

    `npx skills add <owner>/<repo>` writes skills-lock.json next to the .agents
    folder, recording the GitHub repository each skill came from. A skill with
    no lock entry was copied in by hand and is treated as not public.
    """
    urls: dict[str, str] = {}
    for root in skill_paths:
        if not root.is_dir():
            continue
        # <project>/.agents/skills -> <project>/skills-lock.json
        project = root.parent.parent if root.parent.name == ".agents" else root.parent
        lock = project / "skills-lock.json"
        if not lock.is_file():
            continue
        try:
            entries = json.loads(lock.read_text(encoding="utf-8")).get("skills", {})
        except (json.JSONDecodeError, OSError):
            continue
        for name, entry in entries.items():
            if entry.get("sourceType") == "github" and entry.get("source") and entry.get("skillPath"):
                urls.setdefault(name, f"https://github.com/{entry['source']}/blob/main/{entry['skillPath']}")
    return urls


def existing_skill_roots(skill_paths: list[Path]) -> list[Path]:
    return [p for p in skill_paths if p.is_dir() and any(p.glob("**/SKILL.md"))]


def _read_frontmatter(skill_file: Path) -> tuple[str, str]:
    text = skill_file.read_text(encoding="utf-8", errors="replace")
    name, description = skill_file.parent.name, ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
                name = str(meta.get("name") or name)
                description = " ".join(str(meta.get("description") or "").split())[:300]
            except yaml.YAMLError:
                pass
    return name, description


def as_dicts(items: list) -> list[dict]:
    return [asdict(i) for i in items]
