"""Pydantic schemas for the `/workflow/evaluate` endpoint."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class WorkflowEvaluateRequest(BaseModel):
    """Request body for `POST /workflow/evaluate`.

    Triggers the full LangGraph hiring workflow (parse -> match -> score ->
    decide -> conditionally interview/evaluate GitHub -> draft email) for
    an existing candidate.
    """

    candidate_id: uuid.UUID = Field(..., description="Candidate to run the workflow for.")
    github_summary: str | None = Field(
        default=None,
        description="Optional pre-assembled GitHub profile summary. If omitted, only the "
        "candidate's stored GitHub URL is used as minimal context.",
    )


class WorkflowEvaluateResponse(BaseModel):
    """Response body for `POST /workflow/evaluate`.

    Mirrors the relevant fields of the LangGraph `HiringState` after a run,
    serialized as plain JSON-compatible dictionaries.
    """

    parsed_candidate: dict[str, Any] = Field(..., description="Structured resume-parse result.")
    matching_result: dict[str, Any] = Field(..., description="Skill-matching assessment.")
    score_result: dict[str, Any] = Field(..., description="Per-dimension and total score.")
    decision: dict[str, Any] = Field(..., description="Final routing decision and reason.")
    email_content: dict[str, Any] | None = Field(
        default=None, description="Drafted candidate email, if the workflow produced one."
    )
    final_recommendation: str | None = Field(
        default=None, description="Final hire/no-hire recommendation, if the candidate was shortlisted."
    )
