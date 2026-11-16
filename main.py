"""DocumentDB Samples Factory - command line entry point.

    python main.py check                         inventory of tools, skills and MCP servers (no model)
    python main.py run samples/my-sample.md      run the five-stage pipeline for one starter prompt
    python main.py run samples/my-sample.md --requirements requirements/my-sample.md
                                                 ... and score the result against a reference list
    python main.py run --resume runs/x/2026...   continue a run that stopped at a gate
    python main.py aggregate                     roll all runs up into gallery-insights.md
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from factory.config import Settings
from factory.llm import StageError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="main.py", description="Multi-agent pipeline that builds and audits Azure DocumentDB samples.")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the pipeline for one sample prompt.")
    run.add_argument("prompt", nargs="?", type=Path, help="Markdown file containing the sample prompt.")
    run.add_argument("--requirements", type=Path,
                     help="Reference requirements the finished sample is scored against. The builder never sees this file.")
    run.add_argument("--skill", type=Path, help="Shared skill.md context the prompts assume.")
    run.add_argument("--resume", type=Path, help="Run folder to continue; finished stages are skipped.")
    run.add_argument("--yes", action="store_true", help="Approve the build without asking.")
    run.add_argument("--force", action="store_true", help="Continue past an insufficient prompt or a blocked readiness check.")
    run.add_argument("--stop-after", choices=["review", "readiness", "build"], help="Stop after this stage.")
    run.add_argument("--allow-azure-writes", action="store_true", help="Let the builder create and change Azure resources.")

    sub.add_parser("check", help="Show which CLIs, skills and MCP servers are available. Uses no model.")

    agg = sub.add_parser("aggregate", help="Summarize all runs into gallery-insights.md.")
    agg.add_argument("--runs", type=Path, help="Runs folder (default: ./runs).")

    args = parser.parse_args(argv)
    # Quiet two harmless but repetitive messages from the framework's MCP client. Tool failures
    # are still reported, and every tool call is recorded in events.jsonl.
    import logging
    import warnings

    logging.getLogger("agent_framework._mcp").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore", message=".*ping is removed.*")
    for stream in (sys.stdout, sys.stderr):  # model text may hold characters a Windows console cannot print
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    settings = Settings.load()

    try:
        if args.command == "check":
            return asyncio.run(_check(settings))
        if args.command == "aggregate":
            from factory.aggregate import aggregate

            runs_dir = args.runs or settings.runs_dir
            text = aggregate(runs_dir)
            target = runs_dir / "gallery-insights.md"
            runs_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            print(text)
            print(f"Written to {target}")
            return 0

        from factory.pipeline import run_pipeline

        if not args.prompt and not args.resume:
            parser.error("give a prompt file, or --resume <run folder>")
        if args.prompt and not args.prompt.exists():
            parser.error(f"prompt file not found: {args.prompt}")
        if args.requirements and not args.requirements.exists():
            parser.error(f"requirements file not found: {args.requirements}")
        if args.resume and not args.resume.is_dir():
            parser.error(f"run folder not found: {args.resume}")
        if args.allow_azure_writes:
            settings.allow_azure_writes = True
        return asyncio.run(
            run_pipeline(
                settings,
                args.prompt or args.resume / "prompt.md",
                skill_md_path=args.skill,
                requirements_path=args.requirements,
                resume_dir=args.resume,
                assume_yes=args.yes,
                force=args.force,
                stop_after=args.stop_after,
            )
        )
    except StageError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # A model or network failure in the middle of a run. Finished stages are already saved.
        from agent_framework.exceptions import ChatClientException

        if not isinstance(exc, ChatClientException):
            raise
        from factory import pipeline

        reason = str(exc.args[0]) if exc.args else str(exc)
        print(f"\nERROR: the model call failed: {reason.split('service failed to complete the prompt: ')[-1]}", file=sys.stderr)
        if "timed out" in reason.lower():
            print("       The model took longer than FACTORY_REQUEST_TIMEOUT seconds to answer. Raise it in .env, "
                  "or lower FACTORY_MAX_PRIOR_BELIEFS if this was the audit.", file=sys.stderr)
        if pipeline.LAST_RUN_DIR:
            print(f"       Finished stages are saved. Continue with:\n       python main.py run --resume \"{pipeline.LAST_RUN_DIR}\" --yes",
                  file=sys.stderr)
        return 7


async def _check(settings: Settings) -> int:
    from factory.tools import environment, mcp_inventory

    print("Command-line tools")
    for c in [*environment.probe_clis(), environment.probe_azure_login()]:
        print(f"  {'ok ' if c.available else 'NO '} {c.name:<10} {c.detail}")
    skills = environment.find_skills(settings.skill_paths)
    print(f"\nAgent skills ({len(skills)} found)")
    for s in skills:
        print(f"  ok  {s.name}")
    if not skills:
        print("  none found in: " + ", ".join(str(p) for p in settings.skill_paths))
    configs = mcp_inventory.load_mcp_config(settings.mcp_config)
    print(f"\nMCP servers ({settings.mcp_config})")
    missing_required = False
    for status in await mcp_inventory.probe_all(configs):
        flag = "ok " if status.available else "NO "
        print(f"  {flag} {status.name:<12} {status.detail}{' (required)' if status.required else ''}")
        missing_required |= status.required and not status.available
    print(f"\nModel: provider={settings.provider} model={settings.model or '(FACTORY_MODEL not set)'}")
    return 3 if missing_required else 0


if __name__ == "__main__":
    sys.exit(main())
