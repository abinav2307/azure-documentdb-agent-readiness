"""Agent readiness confidence for Azure DocumentDB, computed from stage 2 findings.

The score is calculated by code, not by a model, so the same findings always
give the same score and runs can be compared over time. It measures what the
product team controls: what models already know, whether public sources answer
the questions, whether those sources agree with each other, and whether the
service's own agent tooling is available. Gaps in the machine running the
pipeline (a CLI missing from PATH, for example) are deliberately left out.

If you change the weights or rules, bump SCORE_VERSION so that old and new
scores are not compared as if they were the same measure.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import Confusion, ReadinessReport

SCORE_VERSION = "1"

WEIGHTS = {
    "knowledge": 20,    # what a model gets right before reading anything
    "grounding": 35,    # questions a public source answers
    "consistency": 25,  # questions where public sources do not conflict
    "tooling": 20,      # the service's skills and MCP servers are available
}
GAP_PENALTY = 2         # per information nobody could supply
MAX_GAP_PENALTY = 10

KNOWLEDGE_CREDIT = {"correct": 1.0, "outdated": 0.5, "partly_wrong": 0.5, "wrong": 0.0, "could_not_verify": 0.0}
PRODUCT_TOOL_KINDS = ("skill", "mcp_server")


@dataclass
class Component:
    key: str
    label: str
    measured: str
    share: float
    weight: int
    to_raise: list[str] = field(default_factory=list)

    @property
    def points(self) -> float:
        return round(self.share * self.weight, 1)


@dataclass
class ReadinessScore:
    score: int
    band: str
    components: list[Component]
    gap_penalty: int
    gaps: list[str]
    blocked: bool
    version: str = SCORE_VERSION


def _grounded(c: Confusion) -> bool:
    if c.outcome == "could_not_verify":
        return False
    return any(link.url for link in c.grounding_links) or bool(c.grounding_source.strip()) and "none" not in c.grounding_source.lower()


def _label(c: Confusion) -> str:
    return f"{c.question_id}: {c.question}" if c.question else c.question_id


def score_readiness(report: ReadinessReport) -> ReadinessScore:
    confusions = report.confusions
    n = len(confusions) or 1

    knowledge = Component(
        "knowledge", "Model knowledge before reading anything",
        "Cold answers that were correct (outdated or partly wrong count half)",
        sum(KNOWLEDGE_CREDIT.get(c.outcome, 0.0) for c in confusions) / n if confusions else 0.0,
        WEIGHTS["knowledge"],
        [_label(c) for c in confusions if c.outcome != "correct"],
    )
    ungrounded = [c for c in confusions if not _grounded(c)]
    grounding = Component(
        "grounding", "Public sources answer the questions",
        "Questions answered by a public page or skill",
        (len(confusions) - len(ungrounded)) / n if confusions else 0.0,
        WEIGHTS["grounding"],
        [_label(c) for c in ungrounded],
    )
    conflicting = [c for c in confusions if c.confusion_sources]
    consistency = Component(
        "consistency", "Public sources agree with each other",
        "Questions with no public page stating a conflicting answer",
        (len(confusions) - len(conflicting)) / n if confusions else 0.0,
        WEIGHTS["consistency"],
        [f"{_label(c)} ({len(c.confusion_sources)} conflicting source{'s' if len(c.confusion_sources) != 1 else ''})" for c in conflicting],
    )
    product_tools = [t for t in report.tools if t.kind in PRODUCT_TOOL_KINDS]
    missing_tools = [t for t in product_tools if not t.available]
    tooling = Component(
        "tooling", "Service agent tooling is available",
        "Needed skills and MCP servers that were available",
        (len(product_tools) - len(missing_tools)) / len(product_tools) if product_tools else 1.0,
        WEIGHTS["tooling"],
        [f"{t.name} ({t.kind})" for t in missing_tools],
    )
    components = [knowledge, grounding, consistency, tooling]

    gaps = [g.title or g.description for g in report.information_gaps]
    penalty = min(len(gaps) * GAP_PENALTY, MAX_GAP_PENALTY)
    total = max(0, round(sum(c.points for c in components) - penalty))
    band = "High" if total >= 80 else "Medium" if total >= 60 else "Low"
    return ReadinessScore(total, band, components, penalty, gaps, report.verdict == "blocked")
