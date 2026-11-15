"""Structured outputs for every stage.

Every field is required (no defaults) so the schemas work with strict
structured-output modes. Use an empty string or empty list for "nothing".
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------- stage 1 --

# specified        - the starter prompt says it
# covered_by_skill - the prompt is silent, but an installed skill answers it
# ambiguous        - mentioned, but two builders would do different things
# missing          - neither the prompt nor a skill answers it; the builder will guess
RubricStatus = Literal["specified", "covered_by_skill", "ambiguous", "missing", "not_applicable"]


class RubricItem(BaseModel):
    item: str = Field(description="Rubric item name, exactly as listed in the rubric.")
    status: RubricStatus
    blocking: bool = Field(description="True if the build cannot sensibly start without this.")
    found_in_prompt: str = Field(description="Short quote or paraphrase of what the prompt says. Empty if missing.")
    skill_that_covers: str = Field(description="Name of the installed skill that answers this item. Empty if none.")
    assumption_if_unanswered: str = Field(description="What the builder would assume if nobody answers. Empty if specified.")
    note: str


class PromptReview(BaseModel):
    verdict: Literal["sufficient", "sufficient_with_assumptions", "insufficient"]
    summary: str = Field(description="Two or three sentences a PM can read in ten seconds.")
    rubric: list[RubricItem]
    contradictions: list[str] = Field(description="Places where the prompt disagrees with itself or with skill.md.")
    questions_for_author: list[str] = Field(description="Only questions whose answer would change what gets built.")
    requirements_at_risk: list[str] = Field(
        description="Requirements from the reference file that neither the starter prompt nor a skill leads the builder to. Empty if no reference file."
    )


# ---------------------------------------------------------------- stage 2 --

ConfusedWith = Literal[
    "none",
    "amazon_documentdb",
    "azure_cosmos_db_for_mongodb_ru",
    "azure_cosmos_db_for_nosql",
    "legacy_vcore_naming",
    "open_source_documentdb",
    "mongodb_atlas_or_server",
    "unknown",
]


class QuizAnswer(BaseModel):
    question_id: str
    answer: str
    confidence: Literal["high", "medium", "low"]


class ColdQuiz(BaseModel):
    """Answers given from prior knowledge only, before reading any source."""

    answers: list[QuizAnswer]


class Confusion(BaseModel):
    question_id: str
    question: str
    cold_answer: str
    grounded_answer: str
    grounding_source: str = Field(description="Skill name, doc URL or MCP tool the grounded answer came from. 'none found' if nothing.")
    outcome: Literal["correct", "partly_wrong", "wrong", "could_not_verify"]
    confused_with: ConfusedWith
    why_the_confusion_arose: str = Field(description="The mechanism: shared name, shared namespace, renamed product, shared wire protocol, etc.")
    build_risk: str = Field(description="What would go wrong in the app if the cold answer were used.")


class ToolReadiness(BaseModel):
    name: str
    kind: Literal["mcp_server", "skill", "cli", "credential", "other"]
    needed_for: str
    available: bool
    detail: str = Field(description="Version, tool count, or the error seen.")
    impact_if_missing: str
    workaround: str


class ReadinessReport(BaseModel):
    verdict: Literal["ready", "ready_with_gaps", "blocked"]
    summary: str
    tools: list[ToolReadiness]
    accelerators_missed: list[str] = Field(description="Tools or skills that exist and would speed this build up but are not installed.")
    confusions: list[Confusion]
    information_gaps: list[str] = Field(description="Things the builder needs to know that no skill, doc or tool answered.")
    blockers: list[str]
    guidance_for_builder: list[str] = Field(description="Concrete corrections the builder must apply, drawn from the confusions.")


# ---------------------------------------------------------------- stage 3 --


class BuildReport(BaseModel):
    status: Literal["completed", "partial", "failed"]
    summary: str
    files_created: list[str]
    how_to_run: str
    verification_done: list[str] = Field(description="What was actually executed and passed, e.g. 'pytest: 6 passed'.")
    not_verified: list[str] = Field(description="What could not be run or checked, and why.")
    open_issues: list[str]


# ---------------------------------------------------------------- stage 4 --

ReasonSource = Literal[
    "prompt",            # the sample prompt or skill.md said so
    "skill",             # an installed agent skill said so
    "docs",              # product documentation said so
    "tool_result",       # something observed by running a tool
    "tool_unavailable",  # forced by a missing or failing tool
    "readiness_report",  # a correction from stage 2
    "operator",          # the person running the pipeline decided (gates, flags)
    "model_default",     # no source: the agent's own prior knowledge
]


class Decision(BaseModel):
    id: str
    timestamp: str
    stage: str
    decision: str
    alternatives: list[str]
    reason: str
    reason_source: ReasonSource
    evidence: str


# ---------------------------------------------------------------- stage 5 --


BeliefAbout = Literal["azure_documentdb", "mongodb", "amazon_documentdb", "azure_cosmos_db", "general"]


class PriorBelief(BaseModel):
    id: str = Field(description="K01, K02, ...")
    practice: str = Field(description="One recommendation, stated so an app can be checked against it.")
    category: str
    knowledge_about: BeliefAbout = Field(description="The product this knowledge mainly comes from.")
    confidence_it_holds_for_azure_documentdb: Literal["high", "medium", "low"]


class PriorBeliefs(BaseModel):
    """Best practices recalled from training, written down before any documentation is read."""

    beliefs: list[PriorBelief]


# How a practice stands between the model's prior knowledge and the public record.
Basis = Literal[
    "found_in_public_source",        # public, and not something the model listed beforehand
    "prior_knowledge_confirmed",     # the model knew it, and a public source for this service agrees
    "prior_knowledge_contradicted",  # the model believed otherwise; a public source for this service disagrees
    "prior_knowledge_only",          # the model knows it; no public source for this service says either way
]


class DiscoveredPractice(BaseModel):
    id: str = Field(description="P01, P02, ...")
    practice: str = Field(description="One recommendation, stated so an app can be checked against it.")
    category: str
    basis: Basis
    prior_belief_id: str = Field(description="K01... for the three prior-knowledge values of basis. Empty otherwise.")
    prior_belief: str = Field(description="The prior belief as it was written. Empty if basis is found_in_public_source.")
    prior_belief_about: Literal["none", "azure_documentdb", "mongodb", "amazon_documentdb", "azure_cosmos_db", "general"]
    source_kind: Literal["public_doc", "public_repo", "installed_skill", "local_file", "prior_knowledge"]
    source_name: str = Field(description="Page title or skill name. Empty for prior_knowledge.")
    source_url: str = Field(description="Copied exactly from a tool result or skill text. Empty if you do not have one. Never constructed.")
    how_found: str = Field(description="The search query run or the skill loaded.")
    relevant_to_this_app: bool


class DiscoveredPractices(BaseModel):
    """Open discovery of public guidance, done before the team's checklist is revealed."""

    practices: list[DiscoveredPractice]
    searches_with_no_useful_result: list[str]
    notes: str


# How a practice relates to the team's checklist and to what is publicly findable.
Availability = Literal[
    "discovered_and_listed",     # on the checklist, and open discovery found it: public and discoverable
    "listed_found_by_name_only", # on the checklist, found only by searching for it by name: public but hard to find
    "listed_not_found",          # on the checklist, no public source found: not public, or not written down
    "discovered_not_listed",     # public guidance the checklist does not mention
    "prior_knowledge_only",      # not on the checklist; the model knows it, and no public source backs it
]


class PracticeCheck(BaseModel):
    practice: str
    category: str
    availability: Availability
    discovery_id: str = Field(description="Id of the matching discovered practice (P01...). Empty if none.")
    source_url: str = Field(description="Public URL of the source, copied from the discovered practice or a tool result. Empty if none was found.")
    status: Literal["followed", "violated", "not_assessable", "not_applicable"]
    evidence: str = Field(description="File and line, or the decision id. Empty when not assessable.")
    source: str = Field(description="Page title or skill name. 'checklist only' if no public source backs it.")
    searched: str = Field(description="For not_assessable: what was searched and what was missing.")
    fix: str = Field(description="For violated: the change to make. Otherwise empty.")


class DecisionReview(BaseModel):
    decision_id: str
    assessment: Literal["sound", "questionable", "wrong", "unverifiable"]
    comment: str


class DocGap(BaseModel):
    topic: str
    what_was_missing: str
    where_searched: str
    effect_on_this_build: str
    proposed_fix_type: Literal[
        "learn_doc", "discoverability", "agent_kit_rule", "mcp_tool_or_description", "sample_or_quickstart",
        "naming_or_disambiguation", "other"
    ]
    proposed_content: str = Field(description="Outline of the page, rule or tool description the product team should ship.")
    priority: Literal["high", "medium", "low"]


class RequirementResult(BaseModel):
    requirement: str
    status: Literal["met", "partly_met", "not_met", "not_checkable"]
    evidence: str = Field(description="File and line that shows it, or what is absent.")
    cause: Literal[
        "none",                         # met
        "prompt_silent",                # the starter prompt never asked, and no skill covers it
        "skill_silent",                 # the prompt pointed at the skill, but the skill does not cover it
        "skill_guidance_not_followed",  # a skill covers it and the builder did not follow it
        "builder_error",                # the prompt or skill was clear; the builder got it wrong
        "tool_unavailable",             # a missing or refused tool prevented it
        "could_not_determine",
    ]
    smallest_fix: str = Field(description="The smallest change that would get this met next time: words to add to the starter prompt, a rule to add to a skill, or a tool to supply.")


class AuditReport(BaseModel):
    verdict: Literal["pass", "pass_with_findings", "fail"]
    summary: str
    requirement_results: list[RequirementResult] = Field(description="One per line of the reference requirements. Empty if no reference file.")
    checks: list[PracticeCheck]
    decision_reviews: list[DecisionReview]
    doc_gaps: list[DocGap]
