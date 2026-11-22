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
    ready = ReadinessReport(verdict="ready", summary="", summary_points=[], tools=[], accelerators_missed=[], confusions=[],
                            information_gaps=[], blockers=[], guidance_for_builder=[], inventory_recommendations=[])
    gated = enforce_gates(ctx, review, ready)
    assert gated.verdict == "blocked" and "documentdb" in gated.blockers[0]
    ctx.mcp_statuses = []
    assert enforce_gates(ctx, review, ready).verdict == "ready"


def test_blank_settings_in_env_file_do_not_reach_the_openai_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from factory.llm import make_client

    for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "FACTORY_PROVIDER", "FACTORY_MODEL", "AZURE_OPENAI_ENDPOINT"):
        monkeypatch.delenv(name, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("FACTORY_PROVIDER=openai\nFACTORY_MODEL=some-model\nOPENAI_API_KEY=sk-test\nOPENAI_BASE_URL=\n"
                        "AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com\n")
    client = make_client(Settings.load(env_file))
    assert str(client.client.base_url).startswith("https://api.openai.com/v1")
    for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "FACTORY_PROVIDER", "FACTORY_MODEL", "AZURE_OPENAI_ENDPOINT"):
        monkeypatch.delenv(name, raising=False)


def test_quiz_questions_are_read_from_the_quiz_file() -> None:
    from factory.agents.readiness import quiz_questions

    questions = quiz_questions()
    assert len(questions) == 15 and questions["Q01"].startswith("What is the Azure resource provider namespace")


def test_old_cold_answer_files_still_load() -> None:
    from factory.models import ColdQuiz

    old = ColdQuiz.model_validate_json('{"answers": [{"question_id": "Q01", "answer": "x", "confidence": "high"}]}')
    assert old.answers[0].question == ""


def test_readiness_score_is_deterministic_and_explained() -> None:
    from factory.models import Confusion, InformationGap, Link, ToolReadiness
    from factory.scoring import score_readiness

    def confusion(qid, outcome, link=True, conflict=False):
        return Confusion(question_id=qid, question="q", cold_answer="c", grounded_answer="g",
                         grounding_source="docs" if link else "none found",
                         grounding_links=[Link(title="p", url="https://learn.microsoft.com/x")] if link else [],
                         outcome=outcome, confused_with="none", why_the_confusion_arose="",
                         confusion_sources=[Link(title="old", url="https://example.com")] if conflict else [],
                         build_risk="", improvements=[])

    report = ReadinessReport(
        verdict="ready_with_gaps", summary="", summary_points=[], accelerators_missed=[], blockers=[],
        guidance_for_builder=[], inventory_recommendations=[],
        tools=[ToolReadiness(name="kit", kind="skill", needed_for="", available=True, detail="", impact_if_missing="", workaround="", references=[]),
               ToolReadiness(name="mcp", kind="mcp_server", needed_for="", available=False, detail="", impact_if_missing="", workaround="", references=[]),
               ToolReadiness(name="bicep", kind="cli", needed_for="", available=False, detail="", impact_if_missing="", workaround="", references=[])],
        confusions=[confusion("Q1", "correct"), confusion("Q2", "outdated", conflict=True),
                    confusion("Q3", "wrong"), confusion("Q4", "could_not_verify", link=False)],
        information_gaps=[InformationGap(title="a", description="")],
    )
    first, second = score_readiness(report), score_readiness(report)
    assert first.score == second.score
    by_key = {c.key: c for c in first.components}
    assert by_key["knowledge"].share == 0.375        # (1 + 0.5 + 0 + 0) / 4
    assert by_key["grounding"].share == 0.75         # Q4 not grounded
    assert by_key["consistency"].share == 0.75       # Q2 has a conflicting source
    assert by_key["tooling"].share == 0.5            # the CLI is ignored: it is the machine, not the product
    assert first.gap_penalty == 2
    assert first.score == round(7.5 + 26.2 + 18.8 + 10.0 - 2)   # points are rounded to 0.1 each
    assert first.score == 60 and first.band == "Medium"   # 60 is the bottom of Medium


def test_readiness_reports_from_before_the_new_fields_still_load() -> None:
    old = {"verdict": "ready", "summary": "s", "tools": [], "accelerators_missed": [], "confusions": [],
           "information_gaps": ["gap"], "blockers": [], "guidance_for_builder": ["do x"]}
    report = ReadinessReport.model_validate(old)
    assert report.information_gaps[0].description == "gap" and report.guidance_for_builder[0].instruction == "do x"
    assert report.summary_points == ["s"] and report.inventory_recommendations == []
