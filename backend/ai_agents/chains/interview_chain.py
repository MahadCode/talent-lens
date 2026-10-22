"""Chain that generates one adaptive interview question at a time."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable

from ai_agents.config.llm import get_gemini_llm
from ai_agents.prompts.interview_prompt import interview_prompt
from ai_agents.utils.schemas import InterviewQuestion


def build_interview_chain(llm: BaseChatModel | None = None) -> Runnable[dict, InterviewQuestion]:
    """Build the adaptive interview question chain.

    Args:
        llm: Optional chat model override, primarily for testing.

    Returns:
        A runnable accepting `{"job_description", "candidate_skills",
        "candidate_weaknesses", "conversation_history"}` and returning a
        single validated `InterviewQuestion`.
    """

    model = llm or get_gemini_llm()
    structured_model = model.with_structured_output(InterviewQuestion)
    return interview_prompt | structured_model


def generate_next_question(
    job_description: str,
    candidate_skills: list[str],
    candidate_weaknesses: list[str],
    conversation_history: list[str] | None = None,
    llm: BaseChatModel | None = None,
) -> InterviewQuestion:
    """Generate the next adaptive interview question.

    Args:
        job_description: Free-text job description.
        candidate_skills: Skills demonstrated by the candidate.
        candidate_weaknesses: Skills missing or weak for the candidate.
        conversation_history: Prior Q&A pairs formatted as strings, oldest first.
        llm: Optional chat model override, primarily for testing.

    Returns:
        The next `InterviewQuestion` to ask the candidate.
    """

    chain = build_interview_chain(llm=llm)
    history = conversation_history or []
    return chain.invoke(
        {
            "job_description": job_description,
            "candidate_skills": ", ".join(candidate_skills) if candidate_skills else "None listed",
            "candidate_weaknesses": ", ".join(candidate_weaknesses) if candidate_weaknesses else "None identified",
            "conversation_history": "\n".join(history) if history else "No prior questions yet.",
        }
    )
