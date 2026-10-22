"""Business logic for running the LangGraph hiring workflow.

Per the integration contract, FastAPI routes never call AI agents or the
compiled graph directly — they only ever call `WorkflowService.run(...)`.
This keeps the AI agent layer fully decoupled from HTTP concerns and
means the graph could be swapped for a different implementation without
touching any route.
"""

from __future__ import annotations

import uuid

from ai_agents.graph.hiring_graph import get_compiled_hiring_graph
from ai_agents.graph.state import HiringState
from app.core.constants import CandidateStatus
from app.exceptions.errors import NotFoundError, WorkflowExecutionError
from app.models.candidate import Candidate
from app.models.email_log import EmailLog
from app.models.interview import Interview
from app.models.score import Score
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.email_log_repository import EmailLogRepository
from app.repositories.interview_repository import InterviewRepository
from app.repositories.job_repository import JobRepository
from app.repositories.score_repository import ScoreRepository

_STATUS_BY_DECISION: dict[str, CandidateStatus] = {
    "SHORTLIST": CandidateStatus.SHORTLISTED,
    "MANUAL_REVIEW": CandidateStatus.MANUAL_REVIEW,
    "REJECT": CandidateStatus.REJECTED,
}


class WorkflowService:
    """Runs the compiled LangGraph hiring workflow and persists its results."""

    def __init__(
        self,
        candidate_repo: CandidateRepository,
        job_repo: JobRepository,
        score_repo: ScoreRepository,
        interview_repo: InterviewRepository,
        email_log_repo: EmailLogRepository,
    ) -> None:
        """Initialize the service.

        Args:
            candidate_repo: Repository for `Candidate` persistence.
            job_repo: Repository for `Job` persistence.
            score_repo: Repository for `Score` persistence.
            interview_repo: Repository for `Interview` persistence.
            email_log_repo: Repository for `EmailLog` persistence.
        """

        self._candidate_repo = candidate_repo
        self._job_repo = job_repo
        self._score_repo = score_repo
        self._interview_repo = interview_repo
        self._email_log_repo = email_log_repo

    async def run(self, candidate_id: uuid.UUID, github_summary: str | None = None) -> dict:
        """Run the full hiring workflow for a candidate and persist the results.

        Args:
            candidate_id: The candidate to evaluate. Must already have a
                parsed profile (see `ResumeService.upload_and_parse`).
            github_summary: Optional pre-assembled GitHub profile summary
                used only if the candidate is shortlisted and proceeds to
                GitHub evaluation.

        Returns:
            A plain dict with the fields described by
            `schemas.workflow.WorkflowEvaluateResponse`.

        Raises:
            NotFoundError: If the candidate or its job does not exist, or
                the candidate has not yet been parsed.
            WorkflowExecutionError: If the LangGraph workflow raises an
                unexpected error during execution.
        """

        candidate = await self._candidate_repo.get_by_id(candidate_id)
        if candidate is None:
            raise NotFoundError("Candidate not found.")
        if candidate.parsed_profile is None:
            raise NotFoundError("Candidate has not been parsed yet. Upload a resume first.")

        job = await self._job_repo.get_by_id(candidate.job_id)
        if job is None:
            raise NotFoundError("Job associated with this candidate no longer exists.")

        initial_state: HiringState = {
            "job_description": job.description,
            "job_requirements": job.requirements,
            "resume_text": self._resume_text_placeholder(candidate),
            "parsed_candidate": self._rehydrate_parsed_candidate(candidate),
            "extra": {"github_summary": github_summary} if github_summary else {},
        }

        try:
            graph = get_compiled_hiring_graph()
            final_state = await graph.ainvoke(initial_state)
        except Exception as exc:
            raise WorkflowExecutionError("The hiring workflow failed to execute.") from exc

        await self._persist_results(candidate, final_state)

        return {
            "parsed_candidate": final_state["parsed_candidate"].model_dump(),
            "matching_result": final_state["matching_result"].model_dump(),
            "score_result": final_state["score_result"].model_dump(),
            "decision": final_state["decision"].model_dump(),
            "email_content": (
                final_state["email_content"].model_dump() if final_state.get("email_content") else None
            ),
            "final_recommendation": final_state.get("final_recommendation"),
        }

    def _resume_text_placeholder(self, candidate: Candidate) -> str:
        """Reconstruct a resume-text stand-in for re-running the parser node.

        The parser node re-parses `resume_text` at the start of the graph.
        Since the candidate was already parsed once during upload, we pass
        through the already-extracted profile as a JSON string so the
        parser agent has stable, already-extracted content to work from
        rather than requiring the original file to be re-fetched here.

        Args:
            candidate: The candidate whose stored profile to reuse.

        Returns:
            A JSON string representation of the previously parsed profile.
        """

        import json

        return json.dumps(candidate.parsed_profile)

    def _rehydrate_parsed_candidate(self, candidate: Candidate):
        """Rebuild a `ParsedCandidate` object from the stored JSON profile.

        Args:
            candidate: The candidate whose stored profile to rehydrate.

        Returns:
            A `ParsedCandidate` instance.
        """

        from ai_agents.utils.schemas import ParsedCandidate

        return ParsedCandidate.model_validate(candidate.parsed_profile)

    async def _persist_results(self, candidate: Candidate, final_state: dict) -> None:
        """Persist score, decision-driven status, interview, and email results.

        Args:
            candidate: The candidate the workflow was run for.
            final_state: The final `HiringState` returned by the graph.
        """

        score_result = final_state["score_result"]
        decision = final_state["decision"]

        score = Score(
            candidate_id=candidate.id,
            skills_score=score_result.breakdown.skills_score,
            experience_score=score_result.breakdown.experience_score,
            projects_score=score_result.breakdown.projects_score,
            education_score=score_result.breakdown.education_score,
            certifications_score=score_result.breakdown.certifications_score,
            total_score=score_result.total_score,
            reasoning=score_result.reasoning,
        )
        await self._score_repo.add(score)

        candidate.matching_result = final_state["matching_result"].model_dump()
        candidate.match_percentage = final_state["matching_result"].match_percentage
        candidate.status = _STATUS_BY_DECISION.get(decision.decision.value, candidate.status)

        interview_result = final_state.get("interview_result")
        if interview_result is not None:
            interview = Interview(
                candidate_id=candidate.id,
                questions=[q.model_dump() for q in interview_result.questions_asked],
                overall_assessment=interview_result.overall_assessment,
                passed=interview_result.passed,
            )
            await self._interview_repo.add(interview)
            candidate.status = CandidateStatus.HIRED if interview_result.passed else CandidateStatus.NOT_HIRED

        email_content = final_state.get("email_content")
        if email_content is not None:
            email_log = EmailLog(
                candidate_id=candidate.id,
                email_type=self._infer_email_type(decision, final_state),
                subject=email_content.subject,
                body=email_content.body,
            )
            await self._email_log_repo.add(email_log)

    def _infer_email_type(self, decision, final_state: dict):
        """Infer which `EmailType` was used for logging purposes.

        Args:
            decision: The `DecisionResult` from the workflow.
            final_state: The final `HiringState`.

        Returns:
            The `EmailType` corresponding to the email that was generated.
        """

        from ai_agents.utils.schemas import EmailType

        if decision.decision.value == "REJECT":
            return EmailType.REJECTION
        if final_state.get("final_recommendation"):
            return (
                EmailType.SHORTLIST
                if "Verdict: HIRE" in final_state["final_recommendation"]
                else EmailType.REJECTION
            )
        return EmailType.INTERVIEW_INVITATION
