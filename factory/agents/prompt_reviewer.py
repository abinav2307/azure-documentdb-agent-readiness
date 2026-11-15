"""Stage 1: how far does the starter prompt get a builder, and what fills the rest?"""
from __future__ import annotations

import json

from ..config import load_prompt
from ..context import RunContext
from ..llm import run_agent, skills_provider
from ..models import PromptReview
from ..tools import environment


async def review_prompt(ctx: RunContext) -> PromptReview:
    installed = json.dumps(environment.as_dicts(ctx.skills), indent=1) if ctx.skills else "No agent skills are installed."
    task = (
        f"{ctx.sample_block()}\n\n"
        f"<installed_skills>\n{installed}\n</installed_skills>\n\n"
        f"{ctx.requirements_block()}\n\n"
        f"<rubric>\n{load_prompt('rubric.md')}\n</rubric>\n\n"
        "Review this starter prompt against the rubric and return your review."
    )
    return await run_agent(
        ctx.client_factory(None),
        name="prompt_reviewer",
        instructions=load_prompt("prompt_reviewer.md"),
        task=task,
        output_type=PromptReview,
        context_providers=[skills_provider(ctx.skill_roots)],
        middleware=[ctx.log.trace_middleware("review")],
    )
