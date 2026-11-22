"""Stage 2: do we have the tools and the knowledge to build right now?

Three steps:
1. `collect_inventory` - code, no model: CLIs, sign-in, skills, MCP servers.
2. A "cold" model call with no tools, to record what the model believes about
   the service before it reads anything.
3. A grounded agent that has the skills and MCP servers, compares the cold
   answers with the sources, and writes the readiness report.
"""
from __future__ import annotations

import json
import re

from ..config import load_prompt
from ..context import RunContext
from ..llm import run_agent, skills_provider
from ..models import ColdQuiz, Link, PromptReview, ReadinessReport
from ..tools import environment, mcp_inventory


async def collect_inventory(ctx: RunContext) -> dict:
    """Probe the machine. Fills ctx.skills, ctx.skill_roots and ctx.mcp_statuses."""
    ctx.skills = environment.find_skills(ctx.settings.skill_paths)
    ctx.skill_roots = environment.existing_skill_roots(ctx.settings.skill_paths)
    ctx.mcp_configs = mcp_inventory.load_mcp_config(ctx.settings.mcp_config)
    ctx.mcp_statuses = await mcp_inventory.probe_all(ctx.mcp_configs)
    clis = environment.probe_clis()
    return {
        "command_line_tools": environment.as_dicts(clis),
        "azure_sign_in": environment.as_dicts([environment.probe_azure_login()])[0],
        "skill_folders_searched": [str(p) for p in ctx.settings.skill_paths],
        "installed_skills": environment.as_dicts(ctx.skills),
        "mcp_servers": environment.as_dicts(ctx.mcp_statuses),
        "run_policy": {
            "azure_writes_allowed": ctx.settings.allow_azure_writes,
            "allowed_commands": ctx.settings.allowed_commands,
        },
    }


def quiz_questions() -> dict[str, str]:
    """Question id -> question text, read from confusion_quiz.md."""
    found = re.findall(r"^\s*-\s*\*\*(Q\d+)\*\*\s*(.+?)\s*$", load_prompt("confusion_quiz.md"), re.MULTILINE)
    return {qid: text for qid, text in found}


def with_question_text(cold: ColdQuiz) -> ColdQuiz:
    """Put the exact quiz wording next to each Q answer, whatever the model wrote there."""
    questions = quiz_questions()
    answers = [
        a.model_copy(update={"question": questions[a.question_id]}) if a.question_id in questions else a
        for a in cold.answers
    ]
    return cold.model_copy(update={"answers": answers})


async def cold_quiz(ctx: RunContext) -> ColdQuiz:
    task = (
        f"<quiz>\n{load_prompt('confusion_quiz.md')}\n</quiz>\n\n"
        f"{ctx.sample_block()}\n\n"
        "Answer every quiz question, then add your S01-S05 answers for this sample."
    )
    cold = await run_agent(
        ctx.client_factory(None),
        name="readiness_cold",
        instructions=load_prompt("readiness_cold.md"),
        task=task,
        output_type=ColdQuiz,
    )
    return with_question_text(cold)


async def check_readiness(ctx: RunContext, review: PromptReview, inventory: dict, cold: ColdQuiz) -> ReadinessReport:
    task = (
        f"{ctx.sample_block()}\n\n"
        f"<prompt_review>\n{review.model_dump_json(indent=1)}\n</prompt_review>\n\n"
        f"<machine_inventory>\n{json.dumps(inventory, indent=1)}\n</machine_inventory>\n\n"
        f"<known_accelerators>\n{load_prompt('known_accelerators.md')}\n</known_accelerators>\n\n"
        f"<quiz>\n{load_prompt('confusion_quiz.md')}\n</quiz>\n\n"
        f"<cold_answers>\n{cold.model_dump_json(indent=1)}\n</cold_answers>\n\n"
        "Check the cold answers against your sources and write the readiness report."
    )
    report = await run_agent(
        ctx.client_factory(None),
        name="readiness_checker",
        instructions=load_prompt("readiness_checker.md"),
        task=task,
        output_type=ReadinessReport,
        tools=mcp_inventory.tools_for_stage(ctx.mcp_configs, ctx.mcp_statuses, "readiness"),
        context_providers=[skills_provider(ctx.skill_roots)],
        middleware=[ctx.log.trace_middleware("readiness")],
    )
    return enforce_gates(ctx, review, clean_links(ctx, report))


def clean_links(ctx: RunContext, report: ReadinessReport) -> ReadinessReport:
    """Addresses are set by code: real web addresses are kept, skills get their public GitHub address."""
    skill_urls = environment.skill_public_urls(ctx.settings.skill_paths)

    def fix(links: list[Link]) -> list[Link]:
        fixed = []
        for link in links:
            title, url = link.title.strip(), link.url.strip()
            if not url.startswith(("https://", "http://")):
                url = skill_urls.get(title, "")
            if title or url:
                fixed.append(Link(title=title or url, url=url))
        return fixed

    return report.model_copy(update={
        "confusions": [
            c.model_copy(update={"grounding_links": fix(c.grounding_links), "confusion_sources": fix(c.confusion_sources)})
            for c in report.confusions
        ],
        "tools": [t.model_copy(update={"references": fix(t.references)}) for t in report.tools],
        "guidance_for_builder": [g.model_copy(update={"sources": fix(g.sources)}) for g in report.guidance_for_builder],
        "inventory_recommendations": [
            x.model_copy(update={"references": fix(x.references)}) for x in report.inventory_recommendations
        ],
    })


def enforce_gates(ctx: RunContext, review: PromptReview, report: ReadinessReport) -> ReadinessReport:
    """Rules the model does not get to overrule."""
    blockers = list(report.blockers)
    for status in ctx.mcp_statuses:
        if status.required and not status.available:
            blockers.append(
                f"MCP server '{status.name}' is marked required in mcp.json but did not answer ({status.detail}). "
                "Fix it, or set \"required\": false to build without it."
            )
    if review.verdict == "insufficient":
        blockers.append("The prompt review verdict was 'insufficient'. Answer its questions in the prompt and re-run.")
    blockers = list(dict.fromkeys(blockers))
    if blockers and (report.verdict != "blocked" or blockers != report.blockers):
        report = report.model_copy(update={"verdict": "blocked", "blockers": blockers})
    return report
