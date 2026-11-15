"""Runs the five stages in order, with gates between them.

    1 prompt review  -> stops if the prompt is insufficient
    2 readiness      -> stops if blocked; otherwise asks before building
    3 build
    4 decision log   (written during 1-3, rendered here)
    5 audit

Every stage writes a .json (for machines and for --resume) and a .md (for
people) into the run folder.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, TypeVar

from pydantic import BaseModel

from . import reports
from .agents.auditor import audit_app, discover_practices, reachable_sources, recall_practices
from .agents.builder import build_app
from .agents.prompt_reviewer import review_prompt
from .agents.readiness import check_readiness, cold_quiz, collect_inventory
from .config import Settings
from .context import RunContext
from .decision_log import DecisionLog
from .llm import make_client
from .tools import environment
from .models import AuditReport, BuildReport, ColdQuiz, DiscoveredPractices, PriorBeliefs, PromptReview, ReadinessReport

T = TypeVar("T", bound=BaseModel)

STAGES = ["review", "readiness", "build", "audit"]

EXIT_OK = 0
EXIT_PROMPT_INSUFFICIENT = 2
EXIT_BLOCKED = 3
EXIT_AUDIT_FAILED = 4
EXIT_NOT_APPROVED = 5
EXIT_BUILD_FAILED = 6


def say(message: str) -> None:
    print(message, flush=True)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "sample"


def new_run_dir(settings: Settings, sample_name: str) -> Path:
    run_dir = settings.runs_dir / slug(sample_name) / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _save(run_dir: Path, stem: str, model: BaseModel | dict, markdown: str | None = None) -> None:
    text = model.model_dump_json(indent=2) if isinstance(model, BaseModel) else json.dumps(model, indent=2)
    (run_dir / f"{stem}.json").write_text(text, encoding="utf-8")
    if markdown is not None:
        (run_dir / f"{stem}.md").write_text(markdown, encoding="utf-8")


def _load(run_dir: Path, stem: str, model_type: type[T]) -> T | None:
    path = run_dir / f"{stem}.json"
    return model_type.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None


def _ask(question: str) -> bool:
    if not sys.stdin or not sys.stdin.isatty():
        return False
    return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")


async def run_pipeline(
    settings: Settings,
    prompt_path: Path,
    *,
    skill_md_path: Path | None = None,
    requirements_path: Path | None = None,
    resume_dir: Path | None = None,
    assume_yes: bool = False,
    force: bool = False,
    stop_after: str | None = None,
    client_factory: Callable[[int | None], Any] | None = None,
) -> int:
    sample_name = resume_dir.parent.name if resume_dir else prompt_path.stem
    run_dir = resume_dir or new_run_dir(settings, sample_name)
    if not resume_dir:
        (run_dir / "prompt.md").write_text(prompt_path.read_text(encoding="utf-8"), encoding="utf-8")
    if requirements_path and requirements_path.exists():
        (run_dir / "requirements.md").write_text(requirements_path.read_text(encoding="utf-8"), encoding="utf-8")
    requirements_file = run_dir / "requirements.md"
    prompt_file = run_dir / "prompt.md" if (run_dir / "prompt.md").exists() else prompt_path

    ctx = RunContext(
        settings=settings,
        run_dir=run_dir,
        sample_name=sample_name,
        sample_prompt=prompt_file.read_text(encoding="utf-8"),
        skill_md=skill_md_path.read_text(encoding="utf-8") if skill_md_path and skill_md_path.exists() else "",
        requirements=requirements_file.read_text(encoding="utf-8") if requirements_file.exists() else "",
        log=DecisionLog(run_dir),
        client_factory=client_factory or (lambda max_iterations: make_client(settings, max_iterations)),
    )
    # Skills are found up front: the prompt reviewer needs to know what a skill
    # would fill in before it can say what a short starter prompt leaves open.
    ctx.skills = environment.find_skills(settings.skill_paths)
    ctx.skill_roots = environment.existing_skill_roots(settings.skill_paths)
    say(f"Run folder: {run_dir}")
    say(f"Reference requirements: {'yes' if ctx.requirements else 'none (the audit will check best practices only)'}")

    def finish(code: int, verdicts: dict[str, str]) -> int:
        ctx.log.render_markdown()
        _save(run_dir, "run", {"sample": sample_name, "exit_code": code, "verdicts": verdicts})
        return code

    verdicts: dict[str, str] = {}

    # -- 1. prompt review ---------------------------------------------------
    review = _load(run_dir, "01-prompt-review", PromptReview)
    if review is None:
        say("\n[1/5] Reviewing the prompt ...")
        review = await review_prompt(ctx)
        _save(run_dir, "01-prompt-review", review, reports.prompt_review_md(sample_name, review))
    verdicts["prompt_review"] = review.verdict
    blocking = [r.item for r in review.rubric if r.blocking and r.status in ("missing", "ambiguous")]
    say(f"      Prompt review: {review.verdict}. {review.summary}")
    tally = {s: sum(1 for r in review.rubric if r.status == s) for s in ("specified", "covered_by_skill", "ambiguous", "missing")}
    say(f"      Of {len(review.rubric)} rubric items: {tally['specified']} in the prompt, {tally['covered_by_skill']} covered by a skill, "
        f"{tally['ambiguous'] + tally['missing']} left to the builder.")
    if review.requirements_at_risk:
        say(f"      Requirements at risk: {len(review.requirements_at_risk)}")
    if review.verdict == "insufficient" and not force:
        say("      Blocking items: " + ", ".join(blocking or ["see report"]))
        for q in review.questions_for_author:
            say(f"      ? {q}")
        say("      Stopping. Fix the prompt, or re-run with --force to build on the assumptions.")
        return finish(EXIT_PROMPT_INSUFFICIENT, verdicts)
    if review.verdict == "insufficient":
        ctx.log.add("review", "I continued past an 'insufficient' prompt review", "The run was started with --force",
                    "operator", ["Stop and fix the prompt"], "; ".join(blocking))
    if stop_after == "review":
        return finish(EXIT_OK, verdicts)

    # -- 2. readiness -------------------------------------------------------
    say("\n[2/5] Checking tools and service knowledge ...")
    inventory = await collect_inventory(ctx)  # always re-probed: tools change between runs
    for status in ctx.mcp_statuses:
        say(f"      MCP {status.name}: {'ok, ' + status.detail if status.available else 'UNAVAILABLE - ' + status.detail}")
    say(f"      Agent skills found: {len(ctx.skills)}")
    readiness = _load(run_dir, "02-readiness", ReadinessReport)
    if readiness is None:
        cold = _load(run_dir, "02-cold-answers", ColdQuiz)
        if cold is None:
            cold = await cold_quiz(ctx)
            _save(run_dir, "02-cold-answers", cold)
        readiness = await check_readiness(ctx, review, inventory, cold)
        _save(run_dir, "02-inventory", inventory)
        _save(run_dir, "02-readiness", readiness, reports.readiness_md(sample_name, readiness, inventory, cold))
    verdicts["readiness"] = readiness.verdict
    wrong = [c for c in readiness.confusions if c.outcome in ("wrong", "partly_wrong")]
    say(f"      Readiness: {readiness.verdict}. {readiness.summary}")
    say(f"      Service confusions: {len(wrong)} of {len(readiness.confusions)} answers from memory were wrong or partly wrong.")
    for blocker in readiness.blockers:
        say(f"      ! {blocker}")
    if readiness.verdict == "blocked" and not force:
        say("      Stopping. Clear the blockers, or re-run with --force.")
        return finish(EXIT_BLOCKED, verdicts)
    if stop_after == "readiness":
        return finish(EXIT_OK, verdicts)

    # -- gate: a person approves the build ------------------------------------
    build = _load(run_dir, "03-build", BuildReport)
    if build is None:
        if not assume_yes and not _ask(f"\nReadiness is '{readiness.verdict}'. Build the app now?"):
            say(f"      Not approved. Review 02-readiness.md, then: python main.py run --resume \"{run_dir}\" --yes")
            return finish(EXIT_NOT_APPROVED, verdicts)
        ctx.log.add(
            "readiness",
            f"I approved the build with readiness '{readiness.verdict}'",
            "Approved with --yes" if assume_yes else "Approved at the prompt",
            "operator",
            ["Stop and fix gaps first"],
            "; ".join(readiness.blockers) if readiness.blockers else "",
        )
        for status in ctx.mcp_statuses:
            if not status.available and "build" in status.stages:
                ctx.log.add(
                    "readiness",
                    f"I let the build proceed without the '{status.name}' MCP server",
                    "The server did not answer when probed, and it is not marked required",
                    "tool_unavailable",
                    [f"Fix the '{status.name}' server before building"],
                    status.detail,
                )

        # -- 3. build -----------------------------------------------------------
        say("\n[3/5] Building the app ...")
        build = await build_app(ctx, review, readiness)
        _save(run_dir, "03-build", build, reports.build_md(sample_name, build))
    verdicts["build"] = build.status
    say(f"      Build: {build.status}. {build.summary}")

    # -- 4. decision log ------------------------------------------------------
    decisions = ctx.log.read()
    ctx.log.render_markdown()
    defaults = sum(1 for d in decisions if d.reason_source == "model_default")
    say(f"\n[4/5] Decision log: {len(decisions)} decisions, {defaults} made with no source (model_default).")
    if build.status == "failed" and not force:
        say("      The build failed, so there is nothing to audit.")
        return finish(EXIT_BUILD_FAILED, verdicts)
    if stop_after == "build":
        return finish(EXIT_OK, verdicts)

    # -- 5. audit -------------------------------------------------------------
    audit = _load(run_dir, "05-audit", AuditReport)
    if audit is None:
        sources = reachable_sources(ctx)
        if not sources["documentation_search_available"]:
            say("\n      NOTE: no documentation search server answered. 'Not found' below means not searchable from this machine.")
        discovered = _load(run_dir, "05a-practice-discovery", DiscoveredPractices)
        if discovered is None:
            beliefs = _load(run_dir, "05a-prior-beliefs", PriorBeliefs)
            if beliefs is None:
                say("\n[5/5] Recording what the model already believes (no tools) ...")
                beliefs = await recall_practices(ctx, build)
                _save(run_dir, "05a-prior-beliefs", beliefs)
            say(f"      {len(beliefs.beliefs)} prior beliefs. Finding publicly available best practices (checklist withheld) ...")
            discovered = await discover_practices(ctx, beliefs)
            _save(run_dir, "05a-practice-discovery", discovered, reports.discovery_md(sample_name, discovered, sources))
        with_url = sum(1 for p in discovered.practices if p.source_url)
        say(f"      Found {len(discovered.practices)} practices, {with_url} with a public address.")
        basis = {b: sum(1 for p in discovered.practices if p.basis == b) for b in
                 ("prior_knowledge_confirmed", "prior_knowledge_contradicted", "prior_knowledge_only")}
        say(f"      Prior knowledge: {basis['prior_knowledge_confirmed']} confirmed by public sources, "
            f"{basis['prior_knowledge_contradicted']} contradicted, {basis['prior_knowledge_only']} with no public source.")
        say("      Reconciling with the checklist and auditing the app ...")
        audit = await audit_app(ctx, review, readiness, build, discovered)
        _save(run_dir, "05-audit", audit, reports.audit_md(sample_name, audit, sources))
        (run_dir / "doc-gaps.md").write_text(reports.doc_gaps_md(sample_name, audit.doc_gaps), encoding="utf-8")
    verdicts["audit"] = audit.verdict
    if audit.requirement_results:
        met = sum(1 for r in audit.requirement_results if r.status == "met")
        say(f"      Requirements met: {met} of {len(audit.requirement_results)}.")
    listed = [c for c in audit.checks if c.availability not in ("discovered_not_listed", "prior_knowledge_only")]
    if listed:
        found = sum(1 for c in listed if c.availability == "discovered_and_listed")
        by_name = sum(1 for c in listed if c.availability == "listed_found_by_name_only")
        say(f"      Checklist items: {len(listed)}. Found by open discovery: {found}. Found only by name: {by_name}. "
            f"Not found publicly: {len(listed) - found - by_name}.")
    violated = sum(1 for c in audit.checks if c.status == "violated")
    unknown = sum(1 for c in audit.checks if c.status == "not_assessable")
    say(f"      Audit: {audit.verdict}. {violated} violations, {unknown} not assessable, {len(audit.doc_gaps)} documentation gaps.")
    say(f"\nDone. Open {run_dir / '05-audit.md'} and {run_dir / 'doc-gaps.md'}")
    return finish(EXIT_AUDIT_FAILED if audit.verdict == "fail" else EXIT_OK, verdicts)
