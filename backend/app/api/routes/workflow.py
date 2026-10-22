"""Candidate evaluation endpoint. Reuses the existing LangGraph workflow.

Per the integration contract, this route never touches the AI agent layer
directly — it calls `WorkflowService.run(...)` exclusively.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_workflow_service, require_hr
from app.schemas.workflow import WorkflowEvaluateRequest, WorkflowEvaluateResponse
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflow", tags=["Workflow"], dependencies=[Depends(require_hr())])


@router.post(
    "/evaluate",
    response_model=WorkflowEvaluateResponse,
    status_code=status.HTTP_200_OK,
    summary="Run the full hiring evaluation workflow",
    description=(
        "Runs the complete LangGraph hiring workflow for an already-parsed candidate: "
        "skill matching, scoring, decision, and — for shortlisted candidates — an automated "
        "interview, GitHub evaluation, and final recommendation, followed by email drafting. "
        "HR roles only."
    ),
    responses={
        404: {"description": "Candidate or job not found, or candidate has not been parsed yet."},
        502: {"description": "The LangGraph workflow failed to execute."},
    },
)
async def evaluate_candidate(
    payload: WorkflowEvaluateRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowEvaluateResponse:
    """Run the hiring workflow for a candidate.

    Args:
        payload: The candidate id (and optional GitHub summary) to evaluate.
        workflow_service: Injected `WorkflowService`.

    Returns:
        The parsed candidate, matching result, score, decision, generated
        email, and (if applicable) final recommendation.
    """

    result = await workflow_service.run(
        candidate_id=payload.candidate_id, github_summary=payload.github_summary
    )
    return WorkflowEvaluateResponse(**result)
