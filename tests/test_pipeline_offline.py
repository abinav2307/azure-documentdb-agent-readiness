"""End-to-end pipeline test with a scripted model.

The model is fake; everything else is real: the Agent Framework tool loop,
the file and command tools, a local MCP server, the decision log, the gates
and the reports.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from factory import pipeline
from factory.aggregate import aggregate
from factory.config import Settings
from factory.models import (
    AuditReport, BuilderCorrection, BuildReport, ColdQuiz, Confusion, InformationGap, InventoryRecommendation, Link, DiscoveredPractice, DiscoveredPractices, DocGap, PracticeCheck, DecisionReview, RequirementResult,
    PriorBelief, PriorBeliefs, PromptReview, QuizAnswer, ReadinessReport, RubricItem, ToolReadiness,
)
from tests.fakes import ScriptedChatClient

TESTS_DIR = Path(__file__).resolve().parent


def make_settings(tmp_path: Path, *, stub_required: bool = False, broken_required: bool = False) -> Settings:
    servers = {
        "stub": {
            "purpose": "fake docs", "required": stub_required, "stages": ["readiness", "audit"], "documentation": True,
            "command": sys.executable, "args": [str(TESTS_DIR / "echo_mcp_server.py")],
        },
        "broken": {"purpose": "never starts", "required": broken_required, "stages": ["build"], "command": "no-such-command-xyz"},
    }
    (tmp_path / "mcp.json").write_text(json.dumps({"servers": servers}))
    checklist = tmp_path / "checklist.md"
    checklist.write_text("CHECKLIST-MARKER\n- No secrets in source.\n- Vector index parameters follow guidance.\n- Reuse one client.\n")
    # An installed skill with a lock file (public) and one copied in by hand (not public).
    for name in ("documentdb-connection", "house-rules"):
        folder = tmp_path / ".agents" / "skills" / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Guidance.\n---\nReuse one client.\n")
    (tmp_path / "skills-lock.json").write_text(json.dumps({"version": 2, "skills": {"documentdb-connection": {
        "source": "Azure/documentdb-agent-kit", "sourceType": "github", "skillPath": "skills/connection/SKILL.md"}}}))
    return Settings(
        model="scripted", skill_paths=[tmp_path / ".agents" / "skills"], mcp_config=tmp_path / "mcp.json", checklist=checklist,
        max_prior_beliefs=4, runs_dir=tmp_path / "runs", allowed_commands=["python", "python3", "az", Path(sys.executable).name],
        command_timeout_seconds=60,
    )


def review(verdict: str = "sufficient_with_assumptions") -> PromptReview:
    return PromptReview(
        verdict=verdict, summary="Clear goal; driver version not pinned.",
        rubric=[
            RubricItem(item="Driver and version", status="missing", blocking=verdict == "insufficient", found_in_prompt="",
                       skill_that_covers="", assumption_if_unanswered="Latest pymongo 4.x", note=""),
            RubricItem(item="Queries and indexes", status="covered_by_skill", blocking=False, found_in_prompt="",
                       skill_that_covers="documentdb-vector-search", assumption_if_unanswered="", note=""),
        ],
        contradictions=[], questions_for_author=["Which driver version?"],
        requirements_at_risk=["Unit tests run without a live cluster: the prompt never mentions tests"],
    )


def readiness_report() -> ReadinessReport:
    return ReadinessReport(
        verdict="ready_with_gaps", summary="Can build; no data-plane MCP server.",
        summary_points=["Can build.", "No data-plane MCP server."],
        tools=[
            ToolReadiness(name="broken", kind="mcp_server", needed_for="index checks", available=False,
                          detail="did not start", impact_if_missing="indexes unverified", workaround="unit tests",
                          references=[Link(title="MCP Toolkit", url="https://learn.microsoft.com/azure/documentdb/mcp-toolkit")]),
            ToolReadiness(name="documentdb-connection", kind="skill", needed_for="connection", available=True,
                          detail="loaded", impact_if_missing="", workaround="", references=[]),
            ToolReadiness(name="bicep", kind="cli", needed_for="compile templates", available=False,
                          detail="not on PATH", impact_if_missing="templates unchecked", workaround="az bicep build", references=[]),
        ],
        accelerators_missed=["DocumentDB Agent Kit"],
        confusions=[
            Confusion(
                question_id="Q04", question="Connection string?", cold_answer="mongodb://host:27017",
                grounded_answer="none found", grounding_source="stub_search_docs", grounding_links=[],
                outcome="could_not_verify", confused_with="amazon_documentdb",
                why_the_confusion_arose="Same product name on another cloud.", confusion_sources=[],
                build_risk="Connection fails.", improvements=["State the port on the connect page."]),
            Confusion(
                question_id="Q03", question="Which Bicep resource type?", cold_answer="mongoClusters@2024-07-01",
                grounded_answer="Use 2026-06-01.", grounding_source="quickstart",
                grounding_links=[Link(title="Bicep quickstart", url="https://learn.microsoft.com/azure/documentdb/quickstart-bicep"),
                                 Link(title="documentdb-connection", url="")],
                outcome="outdated", confused_with="none", why_the_confusion_arose="Older samples pin 2024-07-01.",
                confusion_sources=[Link(title="PSRule example", url="https://azure.github.io/PSRule.Rules.Azure/x"),
                                   Link(title="made up", url="not-a-url")],
                build_risk="Older schema.", improvements=["Name the current version in the deployment skill."]),
            Confusion(
                question_id="Q01", question="Resource type?", cold_answer="Microsoft.DocumentDB/mongoClusters",
                grounded_answer="Same.", grounding_source="docs", grounding_links=[], outcome="correct", confused_with="none",
                why_the_confusion_arose="", confusion_sources=[], build_risk="", improvements=[]),
        ],
        information_gaps=[InformationGap(title="IVF sizing", description="Recommended IVF parameters")], blockers=[],
        guidance_for_builder=[BuilderCorrection(
            instruction="Take the connection string from the environment; do not construct it.",
            sources=[Link(title="Connect page", url="https://learn.microsoft.com/azure/documentdb/connect")])],
        inventory_recommendations=[
            InventoryRecommendation(name="bicep", worth_adding=True, recommendation="Install with winget.", references=[]),
            InventoryRecommendation(name="mongosh", worth_adding=False, recommendation="The app is tested with pytest.", references=[]),
            InventoryRecommendation(name="broken", worth_adding=True, recommendation="Fix mcp.json.", references=[]),
        ],
    )


class Script:
    """Plays all four agents, keyed on the structured output type each one asks for."""

    def __init__(self, review_verdict: str = "sufficient_with_assumptions") -> None:
        self.review_verdict = review_verdict
        self.turn: dict[str, int] = {}
        self.seen_tool_results: list[str] = []
        self.prompts: dict[str, str] = {}  # the first user message each agent received

    def __call__(self, messages, response_format):
        name = response_format.__name__
        turn = self.turn[name] = self.turn.get(name, 0) + 1
        self.prompts.setdefault(name, "\n".join(m.text or "" for m in messages))
        for content in messages[-1].contents:
            if getattr(content, "result", None) is not None:
                self.seen_tool_results.append(str(content.result))

        if response_format is PromptReview:
            return review(self.review_verdict)
        if response_format is ColdQuiz:
            return ColdQuiz(answers=[
                QuizAnswer(question_id="Q04", question="model's paraphrase", answer="mongodb://host:27017", confidence="medium"),
                QuizAnswer(question_id="S01", question="What index does this sample need?", answer="vector-ivf", confidence="low"),
            ])
        if response_format is ReadinessReport:
            if turn == 1:
                return [("stub_search_docs", {"query": "Azure DocumentDB connection string"})]
            return readiness_report()
        if response_format is BuildReport:
            if turn == 1:
                return [
                    ("log_decision", {"decision": "I chose pymongo 4.x", "alternatives": ["motor"],
                                      "reason": "Nothing specified a version", "reason_source": "model_default", "evidence": ""}),
                ]
            if turn == 2:
                return [
                    ("write_file", {"path": "app.py", "content": "import os\nprint('ok', bool(os.environ.get('DOCUMENTDB_URI')))\n"}),
                    ("write_file", {"path": "README.md", "content": "# Sample\n"}),
                    ("write_file", {"path": "../escape.txt", "content": "nope"}),
                ]
            if turn == 3:
                return [
                    ("run_command", {"command": f"{Path(sys.executable).name} app.py", "working_folder": "."}),
                    ("run_command", {"command": "az group create --name rg --location westus3", "working_folder": "."}),
                ]
            if turn == 4:
                return [
                    ("log_decision", {"decision": "I wrote a Bicep file instead of provisioning", "alternatives": ["az group create"],
                                      "reason": "The command runner refused Azure writes", "reason_source": "tool_unavailable",
                                      "evidence": "REFUSED: this run may not change Azure resources"}),
                ]
            return BuildReport(status="completed", summary="Built.", files_created=["app.py", "README.md"],
                               how_to_run="python app.py", verification_done=["python app.py: exit 0"],
                               not_verified=["Live cluster"], open_issues=[])
        if response_format is PriorBeliefs:
            def belief(i, practice, about):
                return PriorBelief(id=i, practice=practice, category="general", knowledge_about=about,
                                   confidence_it_holds_for_azure_documentdb="medium")
            return PriorBeliefs(beliefs=[
                belief("K01", "Reuse one client", "mongodb"),
                belief("K02", "Connect on port 27017", "amazon_documentdb"),
                belief("K03", "Use retryable writes", "mongodb"),
                belief("K04", "Never classified by discovery", "general"),
                belief("K05", "Beyond the cap", "general"),
            ])
        if response_format is DiscoveredPractices:
            if turn == 1:
                return [("list_files", {"folder": "."}), ("stub_search_docs", {"query": "Azure DocumentDB best practices"}),
                        ("load_skill", {"skill_name": "documentdb-connection"})]
            def found(i, practice, kind, name, url, basis="found_in_public_source", k="", belief="", about="none"):
                return DiscoveredPractice(id=i, practice=practice, category="general", basis=basis, prior_belief_id=k,
                                          prior_belief=belief, prior_belief_about=about, source_kind=kind, source_name=name,
                                          source_url=url, how_found="search", relevant_to_this_app=True)
            return DiscoveredPractices(
                practices=[
                    found("P01", "Reuse one client", "installed_skill", "documentdb-connection", "https://made-up.example/not-real",
                          "prior_knowledge_confirmed", "K01", "Reuse one client", "mongodb"),
                    found("P05", "Connect on port 10260", "public_doc", "Connect page", "https://learn.microsoft.com/azure/documentdb/connect",
                          "prior_knowledge_contradicted", "K02", "Connect on port 27017", "amazon_documentdb"),
                    found("P06", "Use retryable writes", "public_doc", "MongoDB manual", "https://www.mongodb.com/docs/manual/",
                          "prior_knowledge_only", "K03", "Use retryable writes", "mongodb"),
                    found("P02", "Keep secrets out of source", "public_doc", "Security overview", "https://learn.microsoft.com/azure/documentdb/security"),
                    found("P03", "House style", "installed_skill", "house-rules", "https://made-up.example/house"),
                    found("P04", "Batch bulk loads", "public_doc", "Bulk guidance", "learn page, no address"),
                ],
                searches_with_no_useful_result=["vector index parameters"], notes="")
        if response_format is AuditReport:
            if turn == 1:
                return [("list_files", {"folder": "."}), ("read_file", {"path": "decisions.jsonl", "start_line": 1, "max_lines": 50}),
                        ("stub_search_docs", {"query": "vector index parameters"})]
            return AuditReport(
                verdict="pass_with_findings", summary="Runs; one practice could not be assessed.",
                requirement_results=[
                    RequirementResult(requirement="/search returns ten products", status="met", evidence="app/app.py:1",
                                      cause="none", smallest_fix=""),
                    RequirementResult(requirement="Unit tests run without a live cluster", status="not_met", evidence="no tests folder",
                                      cause="prompt_silent", smallest_fix="Add a testing rule to the agent kit's sample skill"),
                ] if "MARKER-REQUIREMENT" in self.prompts.get("AuditReport", "") else [],
                checks=[
                    PracticeCheck(practice="No secrets in source", category="security", status="followed",
                                  availability="discovered_and_listed", discovery_id="P02", source_url="",
                                  evidence="app/app.py:2", source="Security overview", searched="", fix=""),
                    PracticeCheck(topic="IVF parameter sizing", practice="Vector index parameters follow guidance", category="indexing",
                                  status="not_assessable", availability="listed_not_found", discovery_id="", source_url="not a url",
                                  evidence="", source="checklist only", searched="stub_search_docs: no result", fix="",
                                  sources=[Link(title="should be dropped", url="https://example.com")],
                                  what_would_help="A numLists sizing rule on the vector search page."),
                    PracticeCheck(topic="Client reuse", practice="Reuse one client", category="connection", status="followed",
                                  availability="discovered_and_listed", discovery_id="P01", source_url="",
                                  evidence="app/app.py:1", source="documentdb-connection", searched="", fix="",
                                  sources=[Link(title="Connect page", url="https://learn.microsoft.com/azure/documentdb/connect"),
                                           Link(title="invented", url="nope")],
                                  what_would_help=""),
                    PracticeCheck(topic="Retryable writes", practice="Use retryable writes", category="reliability", status="not_assessable",
                                  availability="prior_knowledge_only", discovery_id="P06", source_url="https://www.mongodb.com/docs/manual/",
                                  evidence="app does not set it", source="", searched="retryable writes Azure DocumentDB", fix="",
                                  sources=[], what_would_help="One sentence on the connect page saying whether retryable writes are supported."),
                    PracticeCheck(practice="Batch bulk loads", category="reliability", status="not_applicable",
                                  availability="discovered_not_listed", discovery_id="P04", source_url="",
                                  evidence="", source="Bulk guidance", searched="", fix=""),
                ],
                decision_reviews=[DecisionReview(decision_id="D003", assessment="unverifiable", comment="No version guidance found.")],
                doc_gaps=[DocGap(topic="Vector index parameters", what_was_missing="Recommended numLists",
                                 where_searched="docs search", effect_on_this_build="Parameter chosen by default",
                                 proposed_fix_type="learn_doc", proposed_content="Page: choosing IVF parameters", priority="high")],
            )
        raise AssertionError(f"unexpected output type {name}")


def run(settings: Settings, script: Script, prompt: Path, **kwargs) -> int:
    return asyncio.run(pipeline.run_pipeline(
        settings, prompt, client_factory=lambda n: ScriptedChatClient(script), **kwargs))


def write_prompt(tmp_path: Path) -> Path:
    prompt = tmp_path / "retail-demo.md"
    prompt.write_text("Build a small Python sample that reads products from Azure DocumentDB.")
    return prompt


def latest_run(settings: Settings) -> Path:
    return sorted((settings.runs_dir / "retail-demo").iterdir())[-1]


def test_full_pipeline(tmp_path: Path) -> None:
    settings, script = make_settings(tmp_path), Script()
    assert run(settings, script, write_prompt(tmp_path), assume_yes=True) == pipeline.EXIT_OK
    run_dir = latest_run(settings)

    assert (run_dir / "05a-practice-discovery.md").exists()
    cold = {a["question_id"]: a for a in json.loads((run_dir / "02-cold-answers.json").read_text())["answers"]}
    assert cold["Q04"]["question"].startswith("What does a connection string look like")   # exact quiz wording
    assert cold["S01"]["question"] == "What index does this sample need?"                   # the model's own
    for name in ["prompt.md", "01-prompt-review.md", "02-readiness.md", "02-cold-answers.json", "02-inventory.json",
                 "03-build.md", "04-decisions.md", "decisions.jsonl", "events.jsonl", "05-audit.md", "doc-gaps.md", "run.json"]:
        assert (run_dir / name).exists(), name

    # The builder's files landed in app/ and nowhere else.
    assert (run_dir / "app" / "app.py").exists() and not (run_dir / "escape.txt").exists()

    # MCP tools really ran, in readiness and audit.
    assert any("No documentation found for: Azure DocumentDB connection string" in r for r in script.seen_tool_results)

    events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
    by_outcome = {(e["stage"], e["tool"], e["outcome"]) for e in events}
    assert ("build", "run_command", "refused") in by_outcome       # az group create
    assert ("build", "run_command", "ok") in by_outcome            # python app.py
    assert ("build", "write_file", "error") in by_outcome          # ../escape.txt
    assert ("readiness", "stub_search_docs", "ok") in by_outcome
    assert ("audit", "read_file", "ok") in by_outcome

    decisions = [json.loads(line) for line in (run_dir / "decisions.jsonl").read_text().splitlines()]
    sources = [d["reason_source"] for d in decisions]
    # Discovery ran before the audit and never saw the checklist; the auditor did.
    assert "CHECKLIST-MARKER" not in script.prompts["PriorBeliefs"]
    assert not any(e["stage"] == "recall" for e in events)          # the recall step has no tools
    assert '"id": "K02"' in script.prompts["DiscoveredPractices"]   # discovery is given the prior beliefs
    assert "CHECKLIST-MARKER" not in script.prompts["DiscoveredPractices"]
    assert "CHECKLIST-MARKER" in script.prompts["AuditReport"] and '"id": "P01"' in script.prompts["AuditReport"]
    assert ("discovery", "load_skill", "ok") in by_outcome and ("discovery", "stub_search_docs", "ok") in by_outcome

    # Public addresses come from the pipeline: the lock file for skills, and only real web addresses otherwise.
    discovered = {p["id"]: p["source_url"] for p in json.loads((run_dir / "05a-practice-discovery.json").read_text())["practices"]}
    assert discovered == {
        "P01": "https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md",
        "P02": "https://learn.microsoft.com/azure/documentdb/security",
        "P03": "",   # skill copied in by hand: no public address, whatever the model claimed
        "P04": "",   # not a web address
        "P05": "https://learn.microsoft.com/azure/documentdb/connect",
        "P06": "",   # prior knowledge only: never public, even though the model attached a MongoDB page
    }
    discovery = json.loads((run_dir / "05a-practice-discovery.json").read_text())
    assert {p["id"]: p["source_kind"] for p in discovery["practices"]}["P06"] == "prior_knowledge"
    assert "did not classify: K04" in discovery["notes"]
    assert "Not checked: K05" in discovery["notes"]                  # over the cap: set aside, and said so
    assert '"id": "K05"' not in script.prompts["DiscoveredPractices"]
    discovery_md = (run_dir / "05a-practice-discovery.md").read_text()
    assert "| The model believed otherwise; public sources contradict it | 1 |" in discovery_md
    assert "**The model believed:** Connect on port 27017 (knowledge of `amazon_documentdb`)" in discovery_md
    assert (run_dir / "05a-prior-beliefs.json").exists()
    checks = {c["practice"]: c for c in json.loads((run_dir / "05-audit.json").read_text())["checks"]}
    assert checks["Reuse one client"]["source_url"].startswith("https://github.com/Azure/documentdb-agent-kit")
    assert checks["Vector index parameters follow guidance"]["source_url"] == ""
    assert checks["Use retryable writes"]["source_url"] == ""       # taken from the cleaned discovery entry
    audit_md = (run_dir / "05-audit.md").read_text()
    assert "| On the checklist, no public source found | 1 |" in audit_md
    assert "| Found publicly, not on the checklist | 1 |" in audit_md
    assert "| Known to the model, no public source, not on the checklist | 1 |" in audit_md
    assert "house-rules" in audit_md and "No documentation search server answered" not in audit_md
    # Leads with the decision review, with each decision's text; everything else is in the appendix.
    assert audit_md.index("## Review of the builder's decisions") < audit_md.index("## Appendix") < audit_md.index("### Public availability")
    assert "| D003 | I chose pymongo 4.x | model_default | unverifiable |" in audit_md
    # Tabulated availability sections with the requested columns.
    assert "#### On the checklist, no public source found\n\n| Topic | Searched | Description |" in audit_md
    assert "| IVF parameter sizing | stub_search_docs: no result | Vector index parameters follow guidance<br>**What would help:** A numLists sizing rule" in audit_md
    assert "#### Known to the model, no public source, not on the checklist\n\n| Topic | Description | What would help |" in audit_md
    assert "| Retryable writes | Use retryable writes | One sentence on the connect page" in audit_md
    assert "#### On the checklist and found by open discovery\n\n| Topic | Description | Sources |" in audit_md
    # Sources: the discovered practice first (skill mapped to its public page), then the model's real links; invented ones dropped.
    assert ("| Client reuse | Reuse one client | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)"
            "<br>[Connect page](https://learn.microsoft.com/azure/documentdb/connect)<br>invented |") in audit_md
    assert "should be dropped" not in audit_md
    assert "| reliability | Batch bulk loads | Bulk guidance |" in audit_md   # old-style check: topic falls back to its category

    # operator approval + pipeline note about the broken server + the builder's two
    assert sources == ["operator", "tool_unavailable", "model_default", "tool_unavailable"]
    assert "broken" in decisions[1]["decision"]

    assert "Vector index parameters" in (run_dir / "doc-gaps.md").read_text()
    verdicts = json.loads((run_dir / "run.json").read_text())["verdicts"]
    assert {k: v for k, v in verdicts.items() if k != "readiness_score"} == {
        "prompt_review": "sufficient_with_assumptions", "readiness": "ready_with_gaps",
        "build": "completed", "audit": "pass_with_findings"}

    readiness_md = (run_dir / "02-readiness.md").read_text()
    # Bullet verdict, score near the top, tools section last.
    assert "- Can build.\n- No data-plane MCP server." in readiness_md
    assert readiness_md.index("Agent readiness confidence") < readiness_md.index("## Service confusions")
    assert readiness_md.rstrip().splitlines()[-1].startswith("| bicep |")
    # Links: real addresses kept, invented ones dropped, skills mapped to their public address.
    assert "[Bicep quickstart](https://learn.microsoft.com/azure/documentdb/quickstart-bicep)" in readiness_md
    assert "Seen in: [PSRule example](https://azure.github.io/PSRule.Rules.Azure/x)<br>made up" in readiness_md
    assert "[documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)" in readiness_md
    assert "**Improve:** Name the current version in the deployment skill." in readiness_md
    assert "| Take the connection string from the environment; do not construct it. | [Connect page](" in readiness_md
    assert "| IVF sizing | Recommended IVF parameters |" in readiness_md
    assert "Not needed for this sample. The app is tested with pytest." in readiness_md
    assert "Answered correctly from memory: Q01." in readiness_md
    run_info = json.loads((run_dir / "run.json").read_text())
    assert run_info["verdicts"]["readiness_score"].endswith("(v1)")

    insights = aggregate(settings.runs_dir)
    assert "`amazon_documentdb`" not in insights             # could_not_verify is not counted as a wrong answer
    assert "Q03 Which Bicep resource type?" in insights        # outdated is
    assert "Q04 Connection string?" in insights and "vector index parameters (1 samples" in insights
    assert "I chose pymongo 4.x" in insights
    assert "Model believed (amazon_documentdb): Connect on port 27017 / Source says: Connect on port 10260 (1 samples)" in insights
    assert "- Vector index parameters follow guidance (1 samples)" in insights.split("no public source found")[1].split("###")[0]


def test_insufficient_prompt_stops_before_any_build(tmp_path: Path) -> None:
    settings, script = make_settings(tmp_path), Script(review_verdict="insufficient")
    assert run(settings, script, write_prompt(tmp_path), assume_yes=True) == pipeline.EXIT_PROMPT_INSUFFICIENT
    run_dir = latest_run(settings)
    assert (run_dir / "01-prompt-review.md").exists() and not (run_dir / "02-readiness.json").exists()
    assert "BuildReport" not in script.turn


def test_required_server_down_blocks_the_build(tmp_path: Path) -> None:
    settings, script = make_settings(tmp_path, broken_required=True), Script()
    assert run(settings, script, write_prompt(tmp_path), assume_yes=True) == pipeline.EXIT_BLOCKED
    readiness = json.loads((latest_run(settings) / "02-readiness.json").read_text())
    assert readiness["verdict"] == "blocked" and "broken" in readiness["blockers"][0]
    assert "BuildReport" not in script.turn


def test_gate_then_resume(tmp_path: Path) -> None:
    settings, script = make_settings(tmp_path), Script()
    prompt = write_prompt(tmp_path)
    # No --yes and no terminal: the run stops at the approval gate.
    assert run(settings, script, prompt) == pipeline.EXIT_NOT_APPROVED
    run_dir = latest_run(settings)
    assert "BuildReport" not in script.turn
    # Resuming skips the finished stages and builds.
    assert run(settings, script, run_dir / "prompt.md", resume_dir=run_dir, assume_yes=True) == pipeline.EXIT_OK
    assert script.turn["PromptReview"] == 1 and script.turn["ReadinessReport"] == 2
    assert (run_dir / "05-audit.md").exists()


def test_reference_requirements_reach_reviewer_and_auditor_but_never_the_builder(tmp_path: Path) -> None:
    settings, script = make_settings(tmp_path), Script()
    requirements = tmp_path / "requirements.md"
    requirements.write_text("- MARKER-REQUIREMENT: unit tests run without a live cluster.\n")
    assert run(settings, script, write_prompt(tmp_path), assume_yes=True, requirements_path=requirements) == pipeline.EXIT_OK
    run_dir = latest_run(settings)

    assert "MARKER-REQUIREMENT" in script.prompts["PromptReview"]
    assert "MARKER-REQUIREMENT" in script.prompts["AuditReport"]
    for agent in ("ColdQuiz", "ReadinessReport", "BuildReport"):
        assert "MARKER-REQUIREMENT" not in script.prompts[agent], agent
    # The builder's file tools are rooted in app/, so it cannot read the copy in the run folder either.
    assert (run_dir / "requirements.md").exists() and not (run_dir / "app" / "requirements.md").exists()
    # The builder is told which skills the review found, and gets only the starter prompt as its spec.
    assert "documentdb-vector-search" in script.prompts["BuildReport"]

    audit = (run_dir / "05-audit.md").read_text()
    assert "1 of 2 met" in audit and "prompt_silent" in audit
    review_md = (run_dir / "01-prompt-review.md").read_text()
    assert "Covered by a skill | 1: Queries and indexes" in review_md and "the prompt never mentions tests" in review_md
    insights = aggregate(settings.runs_dir)
    assert "| retail-demo | 1 of 2 |" in insights and "### prompt_silent (1)" in insights
