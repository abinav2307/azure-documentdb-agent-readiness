"""Unit tests for the deterministic parts. No model, no network."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from factory.agents.readiness import enforce_gates
from factory.config import Settings
from factory.context import RunContext
from factory.decision_log import DecisionLog
from factory.llm import StageError, parse_structured
from factory.models import PromptReview, ReadinessReport
from factory.tools import environment
from factory.tools.mcp_inventory import McpServerStatus, load_mcp_config
from factory.tools.shell import CommandPolicy, split_command
from factory.tools.workspace import Workspace


def test_workspace_refuses_paths_outside_root(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / "app", writable=True)
    assert ws.write_file("src/a.py", "print(1)\n").startswith("Created")
    assert "print(1)" in ws.read_file("src/a.py")
    with pytest.raises(ValueError):
        ws.resolve("../secret.txt")
    with pytest.raises(ValueError):
        ws.resolve(str(tmp_path / "elsewhere.txt"))
    assert "src/a.py:1" in ws.search_text("PRINT")


def test_read_only_workspace_has_no_write_tool(tmp_path: Path) -> None:
    names = {t.name for t in Workspace(tmp_path, writable=False).tools()}
    assert names == {"list_files", "read_file", "search_text"}
    assert "write_file" in {t.name for t in Workspace(tmp_path, writable=True).tools()}


@pytest.mark.parametrize(
    "command, allowed",
    [
        ("python -m pytest -q", True),
        ("rm -rf /", False),
        ("az group create --name rg --location westus3", False),
        ("az group create --name list", False),
        ("az group list --output table", True),
        ("az resource show --ids /subscriptions/x", True),
        ("az deployment group what-if --resource-group rg --template-file main.bicep", True),
        ("az deployment group create --resource-group rg --template-file main.bicep", False),
        ("az group delete --name rg --yes", False),
        ("az --version", True),
        ("azd up", False),
        ("azd provision", False),
        ("azd init --template x", True),
    ],
)
def test_command_policy_without_azure_writes(command: str, allowed: bool) -> None:
    policy = CommandPolicy(["python", "az", "azd"], allow_azure_writes=False)
    assert (policy.check(split_command(command)) is None) is allowed


def test_command_policy_with_azure_writes() -> None:
    policy = CommandPolicy(["az"], allow_azure_writes=True)
    assert policy.check(split_command("az group create --name rg --location westus3")) is None
    assert policy.check(split_command("curl http://example.com")) is not None


def test_decision_log_round_trip(tmp_path: Path) -> None:
    log = DecisionLog(tmp_path)
    log.add("build", "I chose the Azure CLI over ARM", "The MCP server was unavailable", "tool_unavailable", ["ARM REST"], "ENOENT")
    log.add("build", "I chose IVF", "Nothing said which index to use", "model_default")
    with pytest.raises(ValueError):
        log.add("build", "x", "y", "made_up_source")
    decisions = log.read()
    assert [d.id for d in decisions] == ["D001", "D002"]
    text = log.render_markdown()
    assert "model_default" in text and "ENOENT" in text and (tmp_path / "04-decisions.md").exists()


def test_mcp_config_expands_variables_and_reports_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "mcp.json"
    config.write_text(json.dumps({"servers": {
        "a": {"command": "npx", "args": ["x"], "env": {"URI": "${TEST_URI_SET}"}, "required": True},
        "b": {"url": "https://example.com/mcp", "headers": {"Authorization": "Bearer ${TEST_TOKEN_UNSET}"}},
        "c": {"command": "npx", "disabled": True},
    }}))
    monkeypatch.setenv("TEST_URI_SET", "mongodb://localhost")
    monkeypatch.delenv("TEST_TOKEN_UNSET", raising=False)
    a, b = load_mcp_config(config)
    assert a.env["URI"] == "mongodb://localhost" and a.required and not a.missing_variables
    assert b.missing_variables == ["TEST_TOKEN_UNSET"]


def test_parse_structured_handles_fenced_json() -> None:
    review = PromptReview(verdict="sufficient", summary="ok", rubric=[], contradictions=[], questions_for_author=[], requirements_at_risk=[])
    assert parse_structured(f"Here you go:\n```json\n{review.model_dump_json()}\n```", PromptReview) == review
    with pytest.raises(StageError):
        parse_structured("not json", PromptReview)


def test_skill_discovery(tmp_path: Path) -> None:
    skill = tmp_path / "skills" / "documentdb-indexing"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: documentdb-indexing\ndescription: Index guidance.\n---\n# Body\n")
    found = environment.find_skills([tmp_path / "skills", tmp_path / "missing"])
    assert [(s.name, s.description) for s in found] == [("documentdb-indexing", "Index guidance.")]
    assert environment.existing_skill_roots([tmp_path / "skills", tmp_path / "missing"]) == [tmp_path / "skills"]


def test_skill_public_urls_come_from_the_lock_file(tmp_path: Path) -> None:
    (tmp_path / ".agents" / "skills").mkdir(parents=True)
    (tmp_path / "skills-lock.json").write_text(json.dumps({"skills": {
        "documentdb-indexing": {"source": "Azure/documentdb-agent-kit", "sourceType": "github", "skillPath": "skills/indexing/SKILL.md"},
        "from-a-zip": {"source": "somewhere", "sourceType": "local", "skillPath": "x/SKILL.md"},
    }}))
    assert environment.skill_public_urls([tmp_path / ".agents" / "skills"]) == {
        "documentdb-indexing": "https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md"}
    assert environment.skill_public_urls([tmp_path / "nowhere" / "skills"]) == {}


def test_required_mcp_server_blocks_even_if_the_model_says_ready(tmp_path: Path) -> None:
    ctx = RunContext(Settings(), tmp_path, "s", "p", "", DecisionLog(tmp_path), lambda n: None)
    ctx.mcp_statuses = [McpServerStatus("documentdb", "", True, ["build"], False, "npx not found", [])]
    review = PromptReview(verdict="sufficient", summary="", rubric=[], contradictions=[], questions_for_author=[], requirements_at_risk=[])
    ready = ReadinessReport(verdict="ready", summary="", tools=[], accelerators_missed=[], confusions=[],
                            information_gaps=[], blockers=[], guidance_for_builder=[])
    gated = enforce_gates(ctx, review, ready)
    assert gated.verdict == "blocked" and "documentdb" in gated.blockers[0]
    ctx.mcp_statuses = []
    assert enforce_gates(ctx, review, ready).verdict == "ready"
