"""Assembles the complete hiring LangGraph workflow.

Flow:
    START -> parser -> matcher -> scoring -> decision
        -> [conditional]
            REJECT          -> email -> END
            MANUAL_REVIEW   -> END (no automated email)
            SHORTLIST       -> interview -> github -> final_recommendation -> email -> END

Conditional branching is implemented via `add_conditional_edges` and
`router.route_after_decision` rather than `if/else` statements inside any
node, keeping node functions purely about producing state.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ai_agents.graph.nodes import (
    decision_node,
    email_node,
    final_recommendation_node,
    github_node,
    interview_node,
    matcher_node,
    parser_node,
    scoring_node,
)
from ai_agents.graph.router import route_after_decision
from ai_agents.graph.state import HiringState

# Node name constants, used both when adding nodes and when wiring edges,
# to avoid typos causing silent mismatches between the two.
PARSER_NODE: str = "parser"
MATCHER_NODE: str = "matcher"
SCORING_NODE: str = "scoring"
DECISION_NODE: str = "decision"
INTERVIEW_NODE: str = "interview"
GITHUB_NODE: str = "github"
FINAL_RECOMMENDATION_NODE: str = "final_recommendation"
EMAIL_NODE: str = "email"


def build_hiring_graph() -> CompiledStateGraph:
    """Construct and compile the hiring workflow graph.

    Returns:
        A compiled LangGraph graph ready to `.invoke()` with a `HiringState`.
    """

    graph = StateGraph(HiringState)

    graph.add_node(PARSER_NODE, parser_node)
    graph.add_node(MATCHER_NODE, matcher_node)
    graph.add_node(SCORING_NODE, scoring_node)
    graph.add_node(DECISION_NODE, decision_node)
    graph.add_node(INTERVIEW_NODE, interview_node)
    graph.add_node(GITHUB_NODE, github_node)
    graph.add_node(FINAL_RECOMMENDATION_NODE, final_recommendation_node)
    graph.add_node(EMAIL_NODE, email_node)

    graph.add_edge(START, PARSER_NODE)
    graph.add_edge(PARSER_NODE, MATCHER_NODE)
    graph.add_edge(MATCHER_NODE, SCORING_NODE)
    graph.add_edge(SCORING_NODE, DECISION_NODE)

    graph.add_conditional_edges(
        DECISION_NODE,
        route_after_decision,
        {
            "reject_path": EMAIL_NODE,
            "manual_review_path": END,
            "shortlist_path": INTERVIEW_NODE,
        },
    )

    graph.add_edge(INTERVIEW_NODE, GITHUB_NODE)
    graph.add_edge(GITHUB_NODE, FINAL_RECOMMENDATION_NODE)
    graph.add_edge(FINAL_RECOMMENDATION_NODE, EMAIL_NODE)
    graph.add_edge(EMAIL_NODE, END)

    return graph.compile()


@lru_cache(maxsize=1)
def get_compiled_hiring_graph() -> CompiledStateGraph:
    """Return a cached, process-wide compiled hiring graph instance.

    Returns:
        The singleton compiled hiring graph for this process.
    """

    return build_hiring_graph()
