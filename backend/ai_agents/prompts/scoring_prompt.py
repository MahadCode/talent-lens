"""Prompt template for the candidate scoring chain."""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

SCORING_SYSTEM_PROMPT: str = """You are an expert hiring committee member responsible for scoring
candidates objectively.

Given the candidate's profile and the skill-matching assessment, produce scores for each of the
following dimensions on a 0-100 scale: skills, experience, projects, education, certifications.
Then combine them into a total_score (0-100) using this weighting unless the evidence strongly
suggests otherwise:
- Skills: 40%
- Experience: 30%
- Projects: 15%
- Education: 10%
- Certifications: 5%

Rules:
- Base every score strictly on the provided candidate profile and matching result.
- reasoning must explain how each dimension score was derived and how the total was weighted.
- Return ONLY the structured output described by the response schema.
"""

SCORING_HUMAN_PROMPT: str = """Candidate profile (JSON):
---
{parsed_candidate_json}
---

Skill matching result (JSON):
---
{matching_result_json}
---

Score this candidate."""

scoring_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", SCORING_SYSTEM_PROMPT),
        ("human", SCORING_HUMAN_PROMPT),
    ]
)
