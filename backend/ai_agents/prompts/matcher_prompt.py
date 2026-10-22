"""Prompt template for the skill matching chain."""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

MATCHER_SYSTEM_PROMPT: str = """You are an expert technical recruiter specializing in matching candidates
to job requirements.

Compare the candidate's structured profile against the job requirements and produce a
rigorous, evidence-based assessment. Follow these rules strictly:
- Compute a realistic match_percentage between 0 and 100 based on overlap of required
  skills with candidate skills, weighted by how critical each skill is.
- List every required skill the candidate does not demonstrate in missing_skills.
- List every candidate skill that is not required by the job in extra_skills.
- experience_comparison must explicitly compare years/seniority and domain relevance.
- explanation must justify the match_percentage with specific reasoning.
- Return ONLY the structured output described by the response schema.
"""

MATCHER_HUMAN_PROMPT: str = """Job requirements:
---
{job_requirements}
---

Candidate profile (JSON):
---
{parsed_candidate_json}
---

Assess how well this candidate matches the job requirements above."""

matcher_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", MATCHER_SYSTEM_PROMPT),
        ("human", MATCHER_HUMAN_PROMPT),
    ]
)
