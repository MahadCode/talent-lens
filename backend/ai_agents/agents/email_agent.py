"""Email Agent.

Generates professional candidate-facing email content for shortlist,
rejection, and interview-invitation scenarios. This agent only produces
email content; it never sends email, by design.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from ai_agents.chains.email_chain import draft_email
from ai_agents.utils.schemas import EmailContent, EmailType


class EmailAgent:
    """Drafts candidate-facing emails without ever dispatching them."""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the agent.

        Args:
            llm: Optional chat model override, primarily for testing.
        """

        self._llm = llm

    def run(self, email_type: EmailType, candidate_name: str, context: str) -> EmailContent:
        """Generate email content for a candidate.

        Args:
            email_type: One of `EmailType.SHORTLIST`, `EmailType.REJECTION`,
                or `EmailType.INTERVIEW_INVITATION`.
            candidate_name: The candidate's name for personalization.
            context: Supporting context to weave into the email, e.g. the
                decision agent's `reason` or interview scheduling details.

        Returns:
            A validated `EmailContent` instance containing subject and body.
        """

        return draft_email(
            email_type=email_type,
            candidate_name=candidate_name,
            context=context,
            llm=self._llm,
        )
