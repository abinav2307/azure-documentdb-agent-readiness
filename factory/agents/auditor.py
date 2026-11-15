"""Stage 5: audit the result, and measure what guidance is publicly findable.

Three steps, in order:

0. `recall_practices` has no tools. It writes down the best practices a model
   already believes from training, before any documentation is read.
1. `discover_practices` searches public sources for best practices WITHOUT
   seeing the team's checklist, the way an agent building the app would, then
   says how the public record treats each prior belief: confirmed,
   contradicted, or not mentioned.
2. `audit_app` is then given the checklist as an answer key. It reconciles the
   two lists, searches by name for checklist items discovery missed, and
   checks the app.

Keeping the checklist out of step 1 is what separates "public and findable"
from "public, but only if you already know to look for it".
"""
from __future__ import annotations

import json

from ..config import load_prompt
from ..context import RunContext
from ..llm import run_agent, skills_provider
from ..models import AuditReport, BuildReport, DiscoveredPractices, PriorBeliefs, PromptReview, ReadinessReport
from ..tools import environment, mcp_inventory
from ..tools.workspace import Workspace


def reachable_sources(ctx: RunContext) -> dict:
    """What the audit agents can actually search in this run. Collected by code."""
    servers = [s for s in ctx.mcp_statuses if "audit" in s.stages]
    public_urls = environment.skill_public_urls(ctx.settings.skill_paths)
    return {
        "documentation_search_available": any(s.available and s.documentation for s in servers),
        "mcp_servers": [
            {"name": s.name, "documentation": s.documentation, "available": s.available, "detail": s.detail} for s in servers
        ],
        "installed_skills": len(ctx.skills),
        "installed_skills_with_public_address": sum(1 for s in ctx.skills if s.name in public_urls),
        "installed_skills_without_public_address": sorted(s.name for s in ctx.skills if s.name not in public_urls),
    }


def _public(url: str) -> str:
    url = (url or "").strip()
    return url if url.startswith(("https://", "http://")) else ""


async def recall_practices(ctx: RunContext, build: BuildReport) -> PriorBeliefs:
    """What the model believes before it reads anything. No tools, no skills, no checklist."""
    task = (
        f"{ctx.sample_block()}\n\n"
        f"<what_was_built>\n{build.summary}\nFiles: {json.dumps(build.files_created)}\n</what_was_built>\n\n"
        "List the best practices you already know that apply to this app on Azure DocumentDB."
    )
    return await run_agent(
        ctx.client_factory(None),
        name="practice_recall",
        instructions=load_prompt("practice_recall.md"),
        task=task,
        output_type=PriorBeliefs,
    )


async def discover_practices(ctx: RunContext, beliefs: PriorBeliefs) -> DiscoveredPractices:
    """Open discovery. The checklist is deliberately not passed in."""
    app = Workspace(ctx.app_dir, writable=False)
    task = (
        f"{ctx.sample_block()}\n\n"
        f"<sources_reachable>\n{json.dumps(reachable_sources(ctx), indent=1)}\n</sources_reachable>\n\n"
        f"<prior_beliefs>\n{beliefs.model_dump_json(indent=1)}\n</prior_beliefs>\n\n"
        "The built app is your workspace root. Look at what it uses and find every best practice for Azure DocumentDB "
        "that the public sources give you. Only then check each prior belief against the public record. Return all entries."
    )
    found = await run_agent(
        ctx.client_factory(ctx.settings.builder_max_iterations),
        name="practice_discovery",
        instructions=load_prompt("practice_discovery.md"),
        task=task,
        output_type=DiscoveredPractices,
        tools=[*app.tools(), *mcp_inventory.tools_for_stage(ctx.mcp_configs, ctx.mcp_statuses, "audit")],
        context_providers=[skills_provider(ctx.skill_roots)],
        middleware=[ctx.log.trace_middleware("discovery")],
    )
    # The pipeline, not the model, supplies the public address of installed skills.
    skill_urls = environment.skill_public_urls(ctx.settings.skill_paths)
    practices = []
    for p in found.practices:
        url, kind = _public(p.source_url), p.source_kind
        if p.basis == "prior_knowledge_only" or kind == "prior_knowledge":
            # Prior knowledge is never a public source, whatever address came back with it.
            url, kind = "", "prior_knowledge"
        elif kind == "installed_skill":
            url = skill_urls.get(p.source_name.strip(), "")
        elif kind == "local_file":
            url = ""
        practices.append(p.model_copy(update={"source_url": url, "source_kind": kind}))
    # Every prior belief should have been classified. Say so if some were dropped.
    classified = {p.prior_belief_id.strip() for p in practices if p.prior_belief_id.strip()}
    dropped = [b.id for b in beliefs.beliefs if b.id not in classified]
    notes = found.notes
    if dropped:
        notes = (notes + "\n\n" if notes.strip() else "") + (
            "Prior beliefs the discovery step did not classify: " + ", ".join(dropped) + ". See 05a-prior-beliefs.json."
        )
    return found.model_copy(update={"practices": practices, "notes": notes})


async def audit_app(
    ctx: RunContext, review: PromptReview, readiness: ReadinessReport, build: BuildReport, discovered: DiscoveredPractices
) -> AuditReport:
    # Read-only view of the whole run folder: app/, decisions.jsonl, events.jsonl.
    run_folder = Workspace(ctx.run_dir, writable=False)
    checklist = ctx.settings.checklist.read_text(encoding="utf-8") if ctx.settings.checklist.exists() else "(no checklist file)"

    mistaken = [c.model_dump() for c in readiness.confusions if c.outcome != "correct"]
    task = (
        f"{ctx.sample_block()}\n\n"
        f"{ctx.requirements_block()}\n\n"
        f"<requirements_the_review_flagged_at_risk>{json.dumps(review.requirements_at_risk)}</requirements_the_review_flagged_at_risk>\n\n"
        f"<sources_reachable>\n{json.dumps(reachable_sources(ctx), indent=1)}\n</sources_reachable>\n\n"
        f"<discovered_practices>\n{discovered.model_dump_json(indent=1)}\n</discovered_practices>\n\n"
        f"<checklist>\n{checklist}\n</checklist>\n\n"
        f"<builder_report>\n{build.model_dump_json(indent=1)}\n</builder_report>\n\n"
        f"<prompt_review_verdict>{review.verdict}: {review.summary}</prompt_review_verdict>\n\n"
        f"<readiness_findings>\n"
        f"information_gaps: {json.dumps(readiness.information_gaps)}\n"
        f"accelerators_missed: {json.dumps(readiness.accelerators_missed)}\n"
        f"service_confusions: {json.dumps(mistaken, indent=1)}\n"
        f"</readiness_findings>\n\n"
        f"<decision_count>{len(ctx.log.read())} decisions are recorded in decisions.jsonl.</decision_count>\n\n"
        "The run folder is your workspace root. Start with list_files on '.', read the app, "
        "then decisions.jsonl and events.jsonl, and return the audit report."
    )
    audit = await run_agent(
        ctx.client_factory(ctx.settings.builder_max_iterations),
        name="auditor",
        instructions=load_prompt("auditor.md"),
        task=task,
        output_type=AuditReport,
        tools=[*run_folder.tools(), *mcp_inventory.tools_for_stage(ctx.mcp_configs, ctx.mcp_statuses, "audit")],
        context_providers=[skills_provider(ctx.skill_roots)],
        middleware=[ctx.log.trace_middleware("audit")],
    )
    # A check that points at a discovered practice takes that practice's address;
    # anything that is not a real web address is blanked.
    by_id = {p.id: p for p in discovered.practices}
    checks = []
    for c in audit.checks:
        match = by_id.get(c.discovery_id.strip())
        url = match.source_url if match else _public(c.source_url)
        checks.append(c.model_copy(update={"source_url": url}))
    return audit.model_copy(update={"checks": checks})
