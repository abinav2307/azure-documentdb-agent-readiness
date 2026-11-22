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


def _links(links) -> str:
    shown = [_link(l.title or l.url, l.url) for l in links if l.title or l.url]
    return "<br>".join(shown)


def _cell_lines(*parts: str) -> str:
    return "<br>".join(p for p in parts if p and p.strip())


CONFUSION_ORDER = {"wrong": 0, "partly_wrong": 1, "outdated": 2, "could_not_verify": 3, "correct": 4}


def readiness_md(sample: str, r: ReadinessReport, inventory: dict, cold: ColdQuiz) -> str:
    from .scoring import score_readiness

    out = [f"# 2. Build readiness: {sample}", "", f"**Verdict: {r.verdict}**", ""]
    out += [f"- {_cell(p)}" for p in (r.summary_points or [r.summary])] + [""]

    # -- confidence score --------------------------------------------------
    sc = score_readiness(r)
    out += [
        f"## Agent readiness confidence: {sc.score}/100 ({sc.band})",
        "",
        "How well the public record, the agent kit and the service's tooling prepare an agent to build on Azure DocumentDB, "
        f"from this run's findings. Computed by code, not by the model, so runs can be compared (scoring version {sc.version}). "
        "Gaps in the machine running the pipeline are not counted.",
        "",
    ]
    if sc.blocked:
        out += ["> The verdict is **blocked**, so the build should not start whatever the score.", ""]
    out += ["| Component | What it measures | Result | Points | What would raise it |", "|---|---|---|---|---|"]
    for c in sc.components:
        raise_it = "<br>".join(_cell(x) for x in c.to_raise[:8]) + (f"<br>... and {len(c.to_raise) - 8} more" if len(c.to_raise) > 8 else "")
        out.append(f"| {c.label} | {c.measured} | {round(c.share * 100)}% | {c.points} of {c.weight} | {raise_it or 'Nothing in this run'} |")
    out.append(
        f"| Information nobody could supply | {GAP_NOTE} | {len(sc.gaps)} gaps | -{sc.gap_penalty} | "
        f"{'<br>'.join(_cell(g) for g in sc.gaps) or 'Nothing in this run'} |"
    )
    out += ["", "Bands: High 80 and above, Medium 60 to 79, Low below 60.", ""]

    out += ["## Blockers", "", *_bullets(r.blockers), ""]

    # -- service confusions ----------------------------------------------
    counts = {k: sum(1 for c in r.confusions if c.outcome == k) for k in CONFUSION_ORDER}
    out += [
        "## Service confusions",
        "",
        f"The model answered {len(r.confusions)} questions from memory before reading any source: "
        f"{counts['correct']} correct, {counts['outdated']} outdated, {counts['partly_wrong']} partly wrong, "
        f"{counts['wrong']} wrong, {counts['could_not_verify']} could not be verified.",
        "",
    ]
    shown = sorted((c for c in r.confusions if c.outcome != "correct"), key=lambda c: CONFUSION_ORDER[c.outcome])
    if shown:
        out += [
            "| Question | Outcome | From memory | From sources | Why the confusion arose | Risk to the build, and what to improve |",
            "|---|---|---|---|---|---|",
        ]
        for c in shown:
            outcome = c.outcome.replace("_", " ") + (f"<br>confused with `{c.confused_with}`" if c.confused_with != "none" else "")
            sources = _cell_lines(_cell(c.grounded_answer), _links(c.grounding_links) or _cell(c.grounding_source))
            why = _cell_lines(_cell(c.why_the_confusion_arose), ("Seen in: " + _links(c.confusion_sources)) if c.confusion_sources else "")
            risk = _cell_lines(
                ("**Risk:** " + _cell(c.build_risk)) if c.build_risk.strip() else "",
                *(f"**Improve:** {_cell(i)}" for i in c.improvements),
            )
            out.append(f"| **{c.question_id}** {_cell(c.question)} | {outcome} | {_cell(c.cold_answer)} | {sources} | {why} | {risk} |")
        out.append("")
    correct = [c.question_id for c in r.confusions if c.outcome == "correct"]
    if correct:
        out += [f"Answered correctly from memory: {', '.join(correct)}. Details are in `02-readiness.json`.", ""]

    # -- corrections -------------------------------------------------------
    out += ["## Corrections passed to the builder", ""]
    if r.guidance_for_builder:
        out += ["| Correction | Source of information |", "|---|---|"]
        out += [f"| {_cell(g.instruction)} | {_links(g.sources) or 'No public source recorded'} |" for g in r.guidance_for_builder]
    else:
        out.append("None.")
    out.append("")

    # -- information gaps --------------------------------------------------
    out += ["## Information nobody could supply", ""]
    if r.information_gaps:
        out += ["| Title / category | Description |", "|---|---|"]
        out += [f"| {_cell(g.title) if g.title.strip() else '-'} | {_cell(g.description)} |" for g in r.information_gaps]
    else:
        out.append("None.")
    out.append("")

    out += ["## Accelerators not installed", "", *_bullets(r.accelerators_missed), ""]

    # -- machine inventory ---------------------------------------------------
    recs = {x.name.strip().lower(): x for x in r.inventory_recommendations}

    def recommendation(name: str, available: bool) -> str:
        if available:
            return ""
        rec = recs.get(name.strip().lower())
        if not rec:
            return "No recommendation recorded."
        text = _cell(rec.recommendation) if rec.worth_adding else f"Not needed for this sample. {_cell(rec.recommendation)}"
        return _cell_lines(text, _links(rec.references))

    out += [
        "## Machine inventory (collected by code)",
        "",
        "| Item | Available | Detail | Recommendation if missing |",
        "|---|---|---|---|",
    ]
    for c in inventory.get("command_line_tools", []):
        out.append(f"| CLI `{c['name']}` | {'yes' if c['available'] else '**no**'} | {_cell(c['detail'])} | {recommendation(c['name'], c['available'])} |")
    sign_in = inventory.get("azure_sign_in", {})
    out.append(
        f"| Azure sign-in | {'yes' if sign_in.get('available') else '**no**'} | {_cell(sign_in.get('detail', ''))} "
        f"| {recommendation('az login', bool(sign_in.get('available')))} |"
    )
    for s in inventory.get("mcp_servers", []):
        names = ", ".join(t["name"] for t in s["tools"][:12]) + (" ..." if len(s["tools"]) > 12 else "")
        out.append(
            f"| MCP `{s['name']}`{' (required)' if s['required'] else ''} | {'yes' if s['available'] else '**no**'} "
            f"| {_cell(s['detail'])}{': ' + _cell(names) if names else ''} | {recommendation(s['name'], s['available'])} |"
        )
    skills = inventory.get("installed_skills", [])
    out.append(f"| Agent skills | {'yes' if skills else '**no**'} | {_cell(', '.join(x['name'] for x in skills) or 'none found')} | |")
    out.append("")

    # -- tools, last -----------------------------------------------------------
    out += ["## Tools for this sample", "", "| Tool | Kind | Available | Needed for | Detail, if missing, and workaround |", "|---|---|---|---|---|"]
    for t in r.tools:
        details = _cell_lines(
            ("**Detail:** " + _cell(t.detail)) if t.detail.strip() else "",
            ("**If missing:** " + _cell(t.impact_if_missing)) if t.impact_if_missing.strip() else "",
            ("**Workaround:** " + _cell(t.workaround)) if t.workaround.strip() else "",
            ("**References:** " + _links(t.references)) if t.references else "",
        )
        out.append(f"| {_cell(t.name)} | {t.kind} | {'yes' if t.available else '**no**'} | {_cell(t.needed_for)} | {details} |")
    return "\n".join(out) + "\n"


GAP_NOTE = "Each gap subtracts 2 points, up to 10"


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


def _check_sources(c: PracticeCheck) -> str:
    if c.sources:
        return _links(c.sources)
    if c.source_url:
        return _link(c.source, c.source_url)
    return f"{_cell(c.source)} (no public address recorded)" if c.source.strip() else "None recorded"


# Columns for each availability outcome: (heading, cell builder).
AVAILABILITY_COLUMNS = {
    "listed_not_found": [
        ("Topic", lambda c: _cell(c.topic)),
        ("Searched", lambda c: _cell(c.searched) or "-"),
        ("Description", lambda c: _cell_lines(_cell(c.practice), ("**What would help:** " + _cell(c.what_would_help)) if c.what_would_help.strip() else "")),
    ],
    "listed_found_by_name_only": [
        ("Topic", lambda c: _cell(c.topic)),
        ("Searched for", lambda c: _cell_lines(_cell(c.practice), ("**Searches:** " + _cell(c.searched)) if c.searched.strip() else "")),
        ("Sources", _check_sources),
    ],
    "discovered_not_listed": [
        ("Topic", lambda c: _cell(c.topic)),
        ("Description", lambda c: _cell(c.practice)),
        ("Sources", _check_sources),
    ],
    "prior_knowledge_only": [
        ("Topic", lambda c: _cell(c.topic)),
        ("Description", lambda c: _cell(c.practice)),
        ("What would help", lambda c: _cell(c.what_would_help) or "-"),
    ],
    "discovered_and_listed": [
        ("Topic", lambda c: _cell(c.topic)),
        ("Description", lambda c: _cell(c.practice)),
        ("Sources", _check_sources),
    ],
}


def availability_md(checks: list[PracticeCheck], level: str = "##") -> list[str]:
    out = [f"{level} Public availability of best practices", "", "| Outcome | Count | What it means |", "|---|---|---|"]
    for key, title, meaning in AVAILABILITY:
        out.append(f"| {title} | {sum(1 for c in checks if c.availability == key)} | {meaning} |")
    out.append("")
    for key, title, _ in AVAILABILITY:
        rows = [c for c in checks if c.availability == key]
        if not rows:
            continue
        columns = AVAILABILITY_COLUMNS[key]
        out += [f"{level}# {title}", "", "| " + " | ".join(h for h, _ in columns) + " |", "|" + "---|" * len(columns)]
        out += ["| " + " | ".join(cell(c) for _, cell in columns) + " |" for c in rows]
        out.append("")
    return out


def audit_md(sample: str, r: AuditReport, sources: dict | None = None, decisions: list | None = None) -> str:
    counts: dict[str, int] = {}
    for c in r.checks:
        counts[c.status] = counts.get(c.status, 0) + 1
    tally = ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in counts.items()) or "no checks"
    out = [f"# 5. Best-practice audit: {sample}", "", f"**Verdict: {r.verdict}** ({tally})", "", r.summary, ""]

    # -- lead section --------------------------------------------------------
    by_id = {d.id: d for d in (decisions or [])}
    out += ["## Review of the builder's decisions", "", "| Decision | What was decided | Reason came from | Assessment | Comment |", "|---|---|---|---|---|"]
    for d in r.decision_reviews:
        logged = by_id.get(d.decision_id.strip())
        out.append(
            f"| {d.decision_id} | {_cell(logged.decision) if logged else '-'} | {logged.reason_source if logged else '-'} "
            f"| {d.assessment} | {_cell(d.comment)} |"
        )
    if not r.decision_reviews:
        out.append("| - | - | - | - | No decisions reviewed |")
    out += ["", f"Documentation gaps: {len(r.doc_gaps)} (see `doc-gaps.md`).", ""]

    # -- appendix ------------------------------------------------------------
    out += ["## Appendix", ""]
    out += [line.replace("## ", "### ", 1) if line.startswith("## ") else line for line in sources_md(sources)]
    out += availability_md(r.checks, level="###")
    out += ["### How the app measures up", ""]
    for status, title in (
        ("violated", "Violations"),
        ("not_assessable", "Could not be assessed"),
        ("followed", "Followed"),
        ("not_applicable", "Not applicable"),
    ):
        rows = [c for c in r.checks if c.status == status]
        if not rows:
            continue
        out += [f"#### {title}", ""]
        if status == "violated":
            out += ["| Practice | Category | Evidence | Fix | Source |", "|---|---|---|---|---|"]
            out += [f"| {_cell(c.practice)} | {_cell(c.category)} | {_cell(c.evidence)} | {_cell(c.fix)} | {_check_sources(c)} |" for c in rows]
        elif status == "not_assessable":
            out += ["| Practice | Category | What was searched and missing | Source |", "|---|---|---|---|"]
            out += [f"| {_cell(c.practice)} | {_cell(c.category)} | {_cell(c.searched)} | {_check_sources(c)} |" for c in rows]
        else:
            out += ["| Practice | Category | Evidence | Source |", "|---|---|---|---|"]
            out += [f"| {_cell(c.practice)} | {_cell(c.category)} | {_cell(c.evidence)} | {_check_sources(c)} |" for c in rows]
        out.append("")
    if r.requirement_results:
        met = sum(1 for q in r.requirement_results if q.status == "met")
        out += [
            "### Reference requirements",
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
