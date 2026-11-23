"""Roll up many runs into one page of product insights.

A confusion, an unsourced decision or a documentation gap that shows up in one
sample may be a prompt problem. One that shows up across verticals is a
product or documentation problem.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from .decision_log import read_jsonl_lines
from .models import AuditReport, Decision, DiscoveredPractices, ReadinessReport


def latest_runs(runs_dir: Path) -> dict[str, Path]:
    """The most recent run folder for each sample."""
    latest: dict[str, Path] = {}
    if not runs_dir.is_dir():
        return latest
    for sample_dir in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
        runs = sorted(p for p in sample_dir.iterdir() if p.is_dir())
        if runs:
            latest[sample_dir.name] = runs[-1]
    return latest


def aggregate(runs_dir: Path) -> str:
    runs = latest_runs(runs_dir)
    verdict_rows: list[str] = []
    confused_with: Counter[str] = Counter()
    confusion_questions: dict[str, list[str]] = defaultdict(list)
    unverifiable: dict[str, list[str]] = defaultdict(list)
    defaults: list[tuple[str, Decision]] = []
    unavailable: Counter[str] = Counter()
    accelerators: Counter[str] = Counter()
    gaps: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    not_assessable: dict[str, list[str]] = defaultdict(list)
    requirement_rows: list[str] = []
    contradicted: dict[str, list[str]] = defaultdict(list)
    availability: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    unmet_by_cause: dict[str, list[str]] = defaultdict(list)

    for sample, run_dir in runs.items():
        verdicts = {}
        if (run_dir / "run.json").exists():
            verdicts = json.loads((run_dir / "run.json").read_text(encoding="utf-8")).get("verdicts", {})
        verdict_rows.append(
            f"| {sample} | {verdicts.get('prompt_review', '-')} | {verdicts.get('readiness', '-')} | {verdicts.get('readiness_score', '-')} "
            f"| {verdicts.get('build', '-')} | {verdicts.get('audit', '-')} |"
        )
        if (run_dir / "02-readiness.json").exists():
            readiness = ReadinessReport.model_validate_json((run_dir / "02-readiness.json").read_text(encoding="utf-8"))
            for c in readiness.confusions:
                if c.outcome in ("wrong", "partly_wrong", "outdated"):
                    confused_with[c.confused_with] += 1
                    confusion_questions[f"{c.question_id} {c.question}"].append(sample)
                elif c.outcome == "could_not_verify":
                    unverifiable[f"{c.question_id} {c.question}"].append(sample)
            for t in readiness.tools:
                if not t.available:
                    unavailable[f"{t.name} ({t.kind})"] += 1
            accelerators.update(readiness.accelerators_missed)
        if (run_dir / "decisions.jsonl").exists():
            for line in read_jsonl_lines(run_dir / "decisions.jsonl"):
                if line:
                    d = Decision.model_validate_json(line)
                    if d.reason_source == "model_default":
                        defaults.append((sample, d))
        if (run_dir / "05a-practice-discovery.json").exists():
            found = DiscoveredPractices.model_validate_json((run_dir / "05a-practice-discovery.json").read_text(encoding="utf-8"))
            for p in found.practices:
                if p.basis == "prior_knowledge_contradicted":
                    contradicted[f"Model believed ({p.prior_belief_about}): {p.prior_belief} / Source says: {p.practice}"].append(sample)
        if (run_dir / "05-audit.json").exists():
            audit = AuditReport.model_validate_json((run_dir / "05-audit.json").read_text(encoding="utf-8"))
            for g in audit.doc_gaps:
                gaps[g.topic.strip().lower()].append((sample, g.priority, f"{g.proposed_fix_type}: {g.proposed_content}"))
            if audit.requirement_results:
                met = sum(1 for q in audit.requirement_results if q.status == "met")
                requirement_rows.append(f"| {sample} | {met} of {len(audit.requirement_results)} |")
            for q in audit.requirement_results:
                if q.status in ("not_met", "partly_met"):
                    unmet_by_cause[q.cause].append(f"**{sample}**: {q.requirement} - fix: {q.smallest_fix}")
            for c in audit.checks:
                availability[c.availability][c.practice.strip()].append(sample)
            for c in audit.checks:
                if c.status == "not_assessable":
                    not_assessable[c.practice.strip()].append(sample)

    def by_spread(d: dict[str, list]) -> list[tuple[str, list]]:
        return sorted(d.items(), key=lambda kv: -len(kv[1]))

    out = [f"# Gallery insights ({len(runs)} samples, latest run of each)", ""]
    out += ["## Verdicts", "", "| Sample | Prompt | Readiness | Readiness score | Build | Audit |", "|---|---|---|---|---|---|", *verdict_rows, ""]

    out += ["## Reference requirements met from the starter prompt alone", ""]
    out += ["| Sample | Met |", "|---|---|", *requirement_rows, ""] if requirement_rows else ["No runs had a reference requirements file.", ""]
    out += ["## Unmet requirements, by cause", ""]
    for cause, rows in sorted(unmet_by_cause.items(), key=lambda kv: -len(kv[1])):
        out += [f"### {cause} ({len(rows)})", "", *[f"- {r}" for r in rows], ""]
    if not unmet_by_cause:
        out += ["None.", ""]

    out += ["## Which neighbouring service the model mistook this one for", ""]
    out += [f"- `{k}`: {v} wrong, partly wrong or outdated answers" for k, v in confused_with.most_common()] or ["No confusions recorded."]
    out += ["", "## Questions answered wrongly from memory", ""]
    out += [f"- {q} ({len(s)} samples)" for q, s in by_spread(confusion_questions)] or ["None."]
    out += ["", "## Questions no source could answer", ""]
    out += [f"- {q} ({len(s)} samples)" for q, s in by_spread(unverifiable)] or ["None."]

    out += ["", "## Documentation and tooling gaps, by how many samples hit them", ""]
    for topic, hits in by_spread(gaps):
        samples = sorted({h[0] for h in hits})
        top = sorted(hits, key=lambda h: {"high": 0, "medium": 1, "low": 2}[h[1]])[0]
        out += [f"### {topic} ({len(samples)} samples, highest priority: {top[1]})", "", f"- Samples: {', '.join(samples)}", f"- Suggested fix: {top[2]}", ""]
    if not gaps:
        out.append("None.")

    out += ["", "## Where public sources contradict what the model believed", ""]
    out += [f"- {text} ({len(s)} samples)" for text, s in by_spread(contradicted)] or ["None."]

    out += ["", "## Public availability of checklist practices, across samples", ""]
    for key, title in (
        ("listed_not_found", "On the checklist, no public source found"),
        ("listed_found_by_name_only", "On the checklist, found only when searched for by name"),
        ("discovered_not_listed", "Found publicly, not on the checklist"),
        ("prior_knowledge_only", "Known to the model, no public source, not on the checklist"),
    ):
        out += [f"### {title}", ""]
        out += [f"- {p} ({len(s)} samples)" for p, s in by_spread(availability.get(key, {}))] or ["None."]
        out.append("")

    out += ["## Best practices that could not be assessed", ""]
    out += [f"- {p} ({len(s)} samples)" for p, s in by_spread(not_assessable)] or ["None."]

    out += ["", "## Decisions made with no source (`model_default`)", ""]
    out += [f"- **{sample}** {d.id}: {d.decision} - {d.reason}" for sample, d in defaults] or ["None."]

    out += ["", "## Tools that were unavailable", ""]
    out += [f"- {k}: {v} samples" for k, v in unavailable.most_common()] or ["None."]
    out += ["", "## Accelerators not installed", ""]
    out += [f"- {k}: {v} samples" for k, v in accelerators.most_common()] or ["None."]
    return "\n".join(out) + "\n"
