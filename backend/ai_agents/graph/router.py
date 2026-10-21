"""Conditional routing functions for the hiring LangGraph workflow.

Keeping routing logic in its own module (rather than `if/else` blocks
inside node functions) is what LangGraph's `add_conditional_edges` is
designed for, and it keeps each node function focused purely on producing
state, not on deciding graph flow.
"""

from __future__ import annotations

from typing import Literal

from ai_agents.graph.state import HiringState
from ai_agents.utils.schemas import DecisionType

RouteAfterDecision = Literal["reject_path", "shortlist_path", "manual_review_path"]


def route_after_decision(state: HiringState) -> RouteAfterDecision:
    """Route the graph after the decision node based on the decision type.

    `MANUAL_REVIEW` candidates end the automated pipeline without any
    candidate-facing email being generated, since that decision explicitly
    requires human judgment rather than an automatic accept/reject message.
    Only `SHORTLIST` proceeds to interviewing, and only `REJECT` triggers an
    automated rejection email.

    Args:
        state: Current graph state; must contain `decision`.

    Returns:
        `"shortlist_path"` if the candidate was shortlisted, `"reject_path"`
        if rejected, or `"manual_review_path"` if flagged for manual review.
    """

    decision = state["decision"]
    if decision.decision == DecisionType.SHORTLIST:
        return "shortlist_path"
    if decision.decision == DecisionType.REJECT:
        return "reject_path"
    return "manual_review_path"
