"""Chain that evaluates a candidate's GitHub profile summary."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable

from ai_agents.config.llm import get_gemini_llm
from ai_agents.prompts.github_prompt import github_prompt
from ai_agents.utils.schemas import GithubEvaluationResult


def build_github_chain(llm: BaseChatModel | None = None) -> Runnable[dict, GithubEvaluationResult]:
    """Build the GitHub evaluation chain.

    Args:
        llm: Optional chat model override, primarily for testing.

    Returns:
        A runnable accepting `{"github_summary": str}` and returning a
        validated `GithubEvaluationResult`.
    """

    model = llm or get_gemini_llm()
    structured_model = model.with_structured_output(GithubEvaluationResult)
    return github_prompt | structured_model


def evaluate_github_profile(github_summary: str, llm: BaseChatModel | None = None) -> GithubEvaluationResult:
    """Evaluate a candidate's GitHub profile summary.

    Args:
        github_summary: A pre-assembled textual summary of the candidate's
            GitHub profile (repositories, languages, commit history, etc.).
        llm: Optional chat model override, primarily for testing.

    Returns:
        A validated `GithubEvaluationResult` instance.
    """

    chain = build_github_chain(llm=llm)
    return chain.invoke({"github_summary": github_summary})
