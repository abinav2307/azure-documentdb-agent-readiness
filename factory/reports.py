"""Markdown renderings of the stage results, for people to read."""
from __future__ import annotations

from .models import AuditReport, BuildReport, ColdQuiz, DiscoveredPractices, DocGap, PracticeCheck, PromptReview, ReadinessReport


def _cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip() or "-"


def _bullets(items: list[str], empty: str = "None.") -> list[str]:
    return [f"- {i}" for i in items] if items else [empty]


def prompt_review_md(sample: str, r: PromptReview) -> str:
    labels = {
        "specified": "In the prompt",
        "covered_by_skill": "Covered by a skill",
        "ambiguous": "Ambiguous: builder will guess",
        "missing": "Missing: builder will guess",
        "not_applicable": "Not applicable",
    }
    out = [f"# 1. Prompt review: {sample}", "", f"**Verdict: {r.verdict}**", "", r.summary, ""]
    out += ["## Where each answer will come from", "", "| Source | Rubric items |", "|---|---|"]
    for status, label in labels.items():
        names = [i.item for i in r.rubric if i.status == status]
        out.append(f"| {label} | {len(names)}: {_cell(', '.join(names))} |")
    out += ["", "## Reference requirements at risk", "", *_bullets(r.requirements_at_risk, "None flagged, or no reference file was supplied."), ""]
    out += ["## Questions for the prompt author", "", *_bullets(r.questions_for_author), ""]
    out += ["## Contradictions and missing references", "", *_bullets(r.contradictions), ""]
    out += ["## Rubric", "", "| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |", "|---|---|---|---|---|---|---|"]
    for i in r.rubric:
        out.append(
            f"| {_cell(i.item)} | {i.status} | {'yes' if i.blocking else 'no'} | {_cell(i.found_in_prompt)} "
            f"| {_cell(i.skill_that_covers)} | {_cell(i.assumption_if_unanswered)} | {_cell(i.note)} |"
        )
    return "\n".join(out) + "\n"


def readiness_md(sample: str, r: ReadinessReport, inventory: dict, cold: ColdQuiz) -> str:
    out = [f"# 2. Build readiness: {sample}", "", f"**Verdict: {r.verdict}**", "", r.summary, ""]
    out += ["## Blockers", "", *_bullets(r.blockers), ""]
    out += ["## Tools for this sample", "", "| Tool | Kind | Available | Needed for | Detail | If missing | Workaround |", "|---|---|---|---|---|---|---|"]
    for t in r.tools:
        out.append(
            f"| {_cell(t.name)} | {t.kind} | {'yes' if t.available else '**no**'} | {_cell(t.needed_for)} "
            f"| {_cell(t.detail)} | {_cell(t.impact_if_missing)} | {_cell(t.workaround)} |"
        )
    out += ["", "## Accelerators not installed", "", *_bullets(r.accelerators_missed), ""]

    wrong = [c for c in r.confusions if c.outcome in ("wrong", "partly_wrong")]
    unverified = [c for c in r.confusions if c.outcome == "could_not_verify"]
    correct = [c for c in r.confusions if c.outcome == "correct"]
    out += [
        "## Service confusions",
        "",
        f"The model answered {len(r.confusions)} questions from memory before reading any source: "
        f"{len(correct)} correct, {len(wrong)} wrong or partly wrong, {len(unverified)} could not be verified.",
        "",
    ]
    for c in wrong + unverified:
        out += [
            f"### {c.question_id}: {c.question}",
            "",
            f"- **Outcome:** {c.outcome}" + (f", confused with `{c.confused_with}`" if c.confused_with != "none" else ""),
            f"- **From memory:** {c.cold_answer}",
            f"- **From sources:** {c.grounded_answer}",
            f"- **Source:** {c.grounding_source}",
            f"- **Why the confusion arose:** {c.why_the_confusion_arose}",
            f"- **Risk to the build:** {c.build_risk}",
            "",
        ]
    out += ["## Information nobody could supply", "", *_bullets(r.information_gaps), ""]
    out += ["## Corrections passed to the builder", "", *_bullets(r.guidance_for_builder), ""]

    out += ["## Machine inventory (collected by code)", "", "| Item | Available | Detail |", "|---|---|---|"]
    for c in inventory.get("command_line_tools", []):
        out.append(f"| CLI `{c['name']}` | {'yes' if c['available'] else 'no'} | {_cell(c['detail'])} |")
    sign_in = inventory.get("azure_sign_in", {})
    out.append(f"| Azure sign-in | {'yes' if sign_in.get('available') else 'no'} | {_cell(sign_in.get('detail', ''))} |")
    for s in inventory.get("mcp_servers", []):
        names = ", ".join(t["name"] for t in s["tools"][:12]) + (" ..." if len(s["tools"]) > 12 else "")
        out.append(
            f"| MCP `{s['name']}`{' (required)' if s['required'] else ''} | {'yes' if s['available'] else 'no'} "
            f"| {_cell(s['detail'])}{': ' + _cell(names) if names else ''} |"
        )
    skills = inventory.get("installed_skills", [])
    out.append(f"| Agent skills | {'yes' if skills else 'no'} | {_cell(', '.join(s['name'] for s in skills) or 'none found')} |")
    return "\n".join(out) + "\n"


def build_md(sample: str, r: BuildReport) -> str:
    out = [f"# 3. Build report: {sample}", "", f"**Status: {r.status}**", "", r.summary, ""]
    out += ["## How to run", "", r.how_to_run or "Not provided.", ""]
    out += ["## Verified by running", "", *_bullets(r.verification_done, "Nothing was run."), ""]
    out += ["## Not verified", "", *_bullets(r.not_verified), ""]
    out += ["## Open issues", "", *_bullets(r.open_issues), ""]
    out += ["## Files", "", *_bullets([f"`{f}`" for f in r.files_created]), ""]
    return "\n".join(out) + "\n"


def _link(name: str, url: str) -> str:
    return f"[{_cell(name)}]({url})" if url else _cell(name)


def sources_md(sources: dict | None) -> list[str]:
    if not sources:
        return []
    out = ["## Sources that were reachable in this run", ""]
    if not sources.get("documentation_search_available"):
        out += [
            "> **No documentation search server answered.** In this report, \"not found\" means "
            "\"not searchable from this machine\", not \"not public\". Fix the server in `mcp.json` and re-run the audit.",
            "",
        ]
    out += ["| Source | Reachable | Detail |", "|---|---|---|"]
    for s in sources.get("mcp_servers", []):
        kind = "documentation search" if s["documentation"] else "MCP server"
        out.append(f"| `{s['name']}` ({kind}) | {'yes' if s['available'] else '**no**'} | {_cell(s['detail'])} |")
    out.append(
        f"| Installed agent skills | {sources.get('installed_skills', 0)} "
        f"| {sources.get('installed_skills_with_public_address', 0)} have a public address |"
    )
    private = sources.get("installed_skills_without_public_address", [])
    if private:
        out += ["", "Skills with no public address (copied in by hand, so treated as not public): " + ", ".join(f"`{n}`" for n in private)]
    return out + [""]


BASIS = (
    ("prior_knowledge_contradicted", "The model believed otherwise; public sources contradict it",
     "An agent working from memory builds the wrong thing here."),
    ("prior_knowledge_only", "The model knows it; no public source for this service says either way",
     "Agents will act on it. Nothing public says whether they should."),
    ("prior_knowledge_confirmed", "The model knew it, and public sources agree", "Memory and documentation line up."),
    ("found_in_public_source", "Found in public sources only", "Documented; the model did not list it beforehand."),
)


def discovery_md(sample: str, d: DiscoveredPractices, sources: dict | None = None) -> str:
    public = [p for p in d.practices if p.source_url]
    out = [
        f"# 5a. Best practices: prior knowledge against the public record: {sample}",
        "",
        "A model first listed the best practices it knew from training, with no tools. An agent then searched public "
        "sources without the team's checklist, the way an agent building this app would, and checked each prior belief "
        "against what it found.",
        "",
        f"**{len(d.practices)} practices, {len(public)} with a public address.**",
        "",
        "| Outcome | Count | What it means |",
        "|---|---|---|",
    ]
    for key, title, meaning in BASIS:
        out.append(f"| {title} | {sum(1 for p in d.practices if p.basis == key)} | {meaning} |")
    out += ["", *sources_md(sources)]

    contradicted = [p for p in d.practices if p.basis == "prior_knowledge_contradicted"]
    if contradicted:
        out += ["## Where public sources contradict the model", ""]
        for p in contradicted:
            out += [
                f"### {p.id}: {p.practice}",
                "",
                f"- **The model believed:** {p.prior_belief} (knowledge of `{p.prior_belief_about}`)",
                f"- **The source says:** {p.practice}",
                f"- **Source:** {_link(p.source_name, p.source_url)}",
                "",
            ]
    only = [p for p in d.practices if p.basis == "prior_knowledge_only"]
    if only:
        out += ["## Known to the model, with no public source for this service", "",
                "| Id | Practice | Knowledge of | Searches tried |", "|---|---|---|---|"]
        out += [f"| {p.id} | {_cell(p.practice)} | {p.prior_belief_about} | {_cell(p.how_found)} |" for p in only]
        out.append("")

    out += [
        "## All practices",
        "",
        "| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for p in d.practices:
        out.append(
            f"| {p.id} | {_cell(p.practice)} | {_cell(p.category)} | {p.basis} | {_cell(p.source_name)} ({p.source_kind}) "
            f"| {p.source_url or '**none**'} | {_cell(p.how_found)} | {'yes' if p.relevant_to_this_app else 'no'} |"
        )
    out += ["", "## Searches that returned nothing useful", "", *_bullets(d.searches_with_no_useful_result), ""]
    if d.notes.strip():
        out += ["## Notes", "", d.notes.strip(), ""]
    return "\n".join(out) + "\n"


AVAILABILITY = (
    ("listed_not_found", "On the checklist, no public source found", "Not public, or not written down. A documentation gap."),
    ("listed_found_by_name_only", "On the checklist, found only when searched for by name", "Public but hard to find. A discoverability gap."),
    ("discovered_not_listed", "Found publicly, not on the checklist", "Add it to the checklist, or check that the public guidance is what the team intends."),
    ("prior_knowledge_only", "Known to the model, no public source, not on the checklist", "Agents will act on it from memory. Decide whether it holds for this service, then document it either way."),
    ("discovered_and_listed", "On the checklist and found by open discovery", "Public and discoverable."),
)


def availability_md(checks: list[PracticeCheck]) -> list[str]:
    out = ["## Public availability of best practices", "", "| Outcome | Count | What it means |", "|---|---|---|"]
    for key, title, meaning in AVAILABILITY:
        out.append(f"| {title} | {sum(1 for c in checks if c.availability == key)} | {meaning} |")
    out.append("")
    for key, title, _ in AVAILABILITY:
        rows = [c for c in checks if c.availability == key]
        if not rows:
            continue
        out += [f"### {title}", ""]
        for c in rows:
            if key == "listed_not_found":
                where = f"searched: {_cell(c.searched)}"
            elif c.source_url:
                where = _link(c.source, c.source_url)
            else:
                where = f"{_cell(c.source)}, no public address recorded"
            out.append(f"- {c.practice} ({where})")
        out.append("")
    return out


def audit_md(sample: str, r: AuditReport, sources: dict | None = None) -> str:
    counts: dict[str, int] = {}
    for c in r.checks:
        counts[c.status] = counts.get(c.status, 0) + 1
    tally = ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in counts.items()) or "no checks"
    out = [f"# 5. Best-practice audit: {sample}", "", f"**Verdict: {r.verdict}** ({tally})", "", r.summary, ""]
    out += sources_md(sources)
    out += availability_md(r.checks)
    out += ["## How the app measures up", ""]
    for status, title in (
        ("violated", "Violations"),
        ("not_assessable", "Could not be assessed"),
        ("followed", "Followed"),
        ("not_applicable", "Not applicable"),
    ):
        rows = [c for c in r.checks if c.status == status]
        if not rows:
            continue
        out += [f"### {title}", ""]
        if status == "violated":
            out += ["| Practice | Category | Evidence | Fix | Source |", "|---|---|---|---|---|"]
            out += [f"| {_cell(c.practice)} | {_cell(c.category)} | {_cell(c.evidence)} | {_cell(c.fix)} | {_link(c.source, c.source_url)} |" for c in rows]
        elif status == "not_assessable":
            out += ["| Practice | Category | What was searched and missing | Source |", "|---|---|---|---|"]
            out += [f"| {_cell(c.practice)} | {_cell(c.category)} | {_cell(c.searched)} | {_link(c.source, c.source_url)} |" for c in rows]
        else:
            out += ["| Practice | Category | Evidence | Source |", "|---|---|---|---|"]
            out += [f"| {_cell(c.practice)} | {_cell(c.category)} | {_cell(c.evidence)} | {_link(c.source, c.source_url)} |" for c in rows]
        out.append("")
    if r.requirement_results:
        met = sum(1 for q in r.requirement_results if q.status == "met")
        out += [
            "## Reference requirements",
            "",
            f"{met} of {len(r.requirement_results)} met. The builder never saw these; this measures the starter prompt and the skills.",
            "",
            "| Requirement | Status | Cause | Evidence | Smallest fix |",
            "|---|---|---|---|---|",
        ]
        order = {"not_met": 0, "partly_met": 1, "not_checkable": 2, "met": 3}
        for q in sorted(r.requirement_results, key=lambda q: order[q.status]):
            out.append(
                f"| {_cell(q.requirement)} | {q.status} | {'-' if q.cause == 'none' else q.cause} "
                f"| {_cell(q.evidence)} | {_cell(q.smallest_fix)} |"
            )
        out.append("")
    out += ["## Review of the builder's decisions", "", "| Decision | Assessment | Comment |", "|---|---|---|"]
    out += [f"| {d.decision_id} | {d.assessment} | {_cell(d.comment)} |" for d in r.decision_reviews] or ["| - | - | No decisions reviewed |"]
    out += ["", f"Documentation gaps: {len(r.doc_gaps)} (see `doc-gaps.md`).", ""]
    return "\n".join(out) + "\n"


def doc_gaps_md(sample: str, gaps: list[DocGap]) -> str:
    out = [
        f"# Documentation and tooling gaps: {sample}",
        "",
        "Each entry is something an agent needed to know or do while building this sample and could not find. "
        "These are for the product team.",
        "",
    ]
    if not gaps:
        out.append("No gaps were found in this run.")
    order = {"high": 0, "medium": 1, "low": 2}
    for g in sorted(gaps, key=lambda g: order[g.priority]):
        out += [
            f"## [{g.priority}] {g.topic}",
            "",
            f"- **What was missing:** {g.what_was_missing}",
            f"- **Where the agent looked:** {g.where_searched}",
            f"- **Effect on this build:** {g.effect_on_this_build}",
            f"- **Suggested fix ({g.proposed_fix_type}):** {g.proposed_content}",
            "",
        ]
    return "\n".join(out) + "\n"
