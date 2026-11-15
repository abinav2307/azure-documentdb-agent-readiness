"""Stage 3: build the app, logging decisions as they are made."""
from __future__ import annotations

import json

from ..config import load_prompt
from ..context import RunContext
from ..llm import run_agent, skills_provider
from ..models import BuildReport, PromptReview, ReadinessReport
from ..tools import mcp_inventory
from ..tools.shell import CommandPolicy, run_command_tool
from ..tools.workspace import Workspace


async def build_app(ctx: RunContext, review: PromptReview, readiness: ReadinessReport) -> BuildReport:
    workspace = Workspace(ctx.app_dir, writable=True)
    policy = CommandPolicy(ctx.settings.allowed_commands, ctx.settings.allow_azure_writes)

    assumptions = [
        {"item": r.item, "status": r.status, "assumption": r.assumption_if_unanswered}
        for r in review.rubric
        if r.status in ("ambiguous", "missing") and r.assumption_if_unanswered
    ]
    skills_to_load = sorted({r.skill_that_covers for r in review.rubric if r.status == "covered_by_skill" and r.skill_that_covers})
    task = (
        f"{ctx.sample_block()}\n\n"
        f"<skills_the_review_found_relevant>{json.dumps(skills_to_load)}</skills_the_review_found_relevant>\n\n"
        f"<assumptions_from_prompt_review>\n{json.dumps(assumptions, indent=1)}\n</assumptions_from_prompt_review>\n\n"
        f"<readiness_report>\n{readiness.model_dump_json(indent=1, exclude={'confusions'})}\n</readiness_report>\n\n"
        f"<run_policy>Azure resource changes allowed: {ctx.settings.allow_azure_writes}. "
        f"Allowed commands: {', '.join(ctx.settings.allowed_commands)}.</run_policy>\n\n"
        "Build the sample in the workspace. Log each decision before acting on it, verify by running, "
        "then return the build report."
    )
    tools = [
        *workspace.tools(),
        run_command_tool(workspace, policy, ctx.settings.command_timeout_seconds),
        ctx.log.tool_for("build"),
        *mcp_inventory.tools_for_stage(ctx.mcp_configs, ctx.mcp_statuses, "build"),
    ]
    return await run_agent(
        ctx.client_factory(ctx.settings.builder_max_iterations),
        name="builder",
        instructions=load_prompt("builder.md"),
        task=task,
        output_type=BuildReport,
        tools=tools,
        context_providers=[skills_provider(ctx.skill_roots)],
        middleware=[ctx.log.trace_middleware("build")],
    )
