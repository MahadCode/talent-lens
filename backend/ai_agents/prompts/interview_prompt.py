"""Prompt template for the adaptive interview question chain."""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

INTERVIEW_SYSTEM_PROMPT: str = """You are an expert technical interviewer conducting an adaptive,
one-question-at-a-time interview.

Rules:
- Generate exactly ONE question per call, never a list.
- Base the question on the job description, the candidate's demonstrated skills, and any
  known weaknesses (e.g. missing skills from the matching stage).
- If prior questions and answers are provided, decide whether a follow_up question that probes
  deeper into the previous answer is more valuable than a new topic, and set is_follow_up
  accordingly.
- Vary focus areas across the interview rather than repeating the same topic every time.
- Return ONLY the structured output described by the response schema.
"""

INTERVIEW_HUMAN_PROMPT: str = """Job description:
---
{job_description}
---

Candidate skills:
---
{candidate_skills}
---

Candidate weaknesses (missing skills):
---
{candidate_weaknesses}
---

Prior questions and answers so far (may be empty):
---
{conversation_history}
---

Generate the next interview question."""

interview_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", INTERVIEW_SYSTEM_PROMPT),
        ("human", INTERVIEW_HUMAN_PROMPT),
    ]
)
