"""GitHub Evaluation Agent.

Evaluates a candidate's GitHub profile summary (assumed already collected
by an upstream integration) for repository quality, language breadth,
commit consistency, AI/ML project presence, documentation, and code
quality.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from ai_agents.chains.github_chain import evaluate_github_profile
from ai_agents.utils.schemas import GithubEvaluationResult


class GithubEvaluationAgent:
    """Scores a candidate's GitHub profile summary as a hiring signal."""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the agent.

        Args:
            llm: Optional chat model override, primarily for testing.
        """

        self._llm = llm

    def run(self, github_summary: str) -> GithubEvaluationResult:
        """Evaluate a candidate's GitHub profile.

        Args:
            github_summary: Pre-assembled textual summary of the
                candidate's GitHub profile.

        Returns:
            A validated `GithubEvaluationResult` instance.

        Raises:
            ValueError: If `github_summary` is empty or whitespace-only.
        """

        if not github_summary or not github_summary.strip():
            raise ValueError("github_summary must be a non-empty string.")

        return evaluate_github_profile(github_summary=github_summary, llm=self._llm)
