"""Chain that drafts candidate-facing emails. Never sends email."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable

from ai_agents.config.llm import get_gemini_llm
from ai_agents.prompts.email_prompt import email_prompt
from ai_agents.utils.schemas import EmailContent, EmailType


def build_email_chain(llm: BaseChatModel | None = None) -> Runnable[dict, EmailContent]:
    """Build the email drafting chain.

    Args:
        llm: Optional chat model override, primarily for testing.

    Returns:
        A runnable accepting `{"email_type", "candidate_name", "context"}`
        and returning a validated `EmailContent`.
    """

    model = llm or get_gemini_llm()
    structured_model = model.with_structured_output(EmailContent)
    return email_prompt | structured_model


def draft_email(
    email_type: EmailType,
    candidate_name: str,
    context: str,
    llm: BaseChatModel | None = None,
) -> EmailContent:
    """Draft a candidate-facing email.

    Args:
        email_type: Which kind of email to draft.
        candidate_name: The candidate's name for personalization.
        context: Supporting context (e.g. decision reason, interview slot details)
            to weave into the email.
        llm: Optional chat model override, primarily for testing.

    Returns:
        A validated `EmailContent` instance containing subject and body.
    """

    chain = build_email_chain(llm=llm)
    return chain.invoke(
        {
            "email_type": email_type.value,
            "candidate_name": candidate_name or "Candidate",
            "context": context,
        }
    )
