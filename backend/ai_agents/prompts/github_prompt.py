"""Prompt template for the GitHub evaluation chain."""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

GITHUB_SYSTEM_PROMPT: str = """You are an expert engineering manager evaluating a candidate's
GitHub profile summary.

Evaluate the profile summary provided and assess:
- Repository quality (structure, breadth, relevance to the job)
- Languages used
- Commit consistency (frequency and recency of contributions)
- Presence of AI/ML projects
- Documentation quality (READMEs, usage instructions)
- Code quality (based on any described patterns, tests, reviews)

Rules:
- Base every judgment strictly on the provided profile summary; do not assume access to the
  repositories beyond what is described.
- score must be a single 0-100 number reflecting overall GitHub strength as a hiring signal.
- explanation must justify the score with specific references to the summary provided.
- Return ONLY the structured output described by the response schema.
"""

GITHUB_HUMAN_PROMPT: str = """GitHub profile summary:
---
{github_summary}
---

Evaluate this GitHub profile."""

github_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", GITHUB_SYSTEM_PROMPT),
        ("human", GITHUB_HUMAN_PROMPT),
    ]
)
