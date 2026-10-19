"""Prompt template for the resume parsing chain.

Prompts are kept separate from agent/chain logic so wording can be tuned
or A/B tested without touching business logic.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

PARSER_SYSTEM_PROMPT: str = """You are an expert technical recruiter and resume-parsing assistant.

Extract structured information from the raw resume text provided by the user.
Follow these rules strictly:
- Only extract information explicitly present in the resume text. Do not invent details.
- If a field cannot be found, leave it null (for scalars) or an empty list (for lists).
- Normalize skills to their common names (e.g. "JS" -> "JavaScript").
- Each entry in "experience", "education", "projects", and "certifications" should be a
  single concise string summarizing that entry.
- Return ONLY the structured output described by the response schema. Do not include any
  commentary, markdown formatting, or explanation outside the structured output.
"""

PARSER_HUMAN_PROMPT: str = """Resume text:
---
{resume_text}
---

Extract the candidate's structured profile from the resume text above."""

parser_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", PARSER_SYSTEM_PROMPT),
        ("human", PARSER_HUMAN_PROMPT),
    ]
)
