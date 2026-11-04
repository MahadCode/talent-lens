"""The hiring workflow must keep the matcher explanation, not only the percentage."""

from __future__ import annotations

import uuid

from ai_agents.utils.schemas import DecisionResult, DecisionType, MatchingResult, ScoreBreakdown, ScoringResult
from app.core.constants import CandidateStatus
from app.models.candidate import Candidate
from app.services.workflow_service import WorkflowService
from tests.fakes import MemoryCandidateRepo, MemoryScoreRepo


class _UnusedRepo:
    async def add(self, entity):
        return entity

    async def get_by_id(self, entity_id):
        return None


async def test_persist_results_stores_the_matching_result() -> None:
    candidate = Candidate(job_id=uuid.uuid4(), status=CandidateStatus.PARSED, score_overridden=False)
    candidate.id = uuid.uuid4()
    scores = MemoryScoreRepo()
    service = WorkflowService(
        candidate_repo=MemoryCandidateRepo(),
        job_repo=_UnusedRepo(),
        score_repo=scores,
        interview_repo=_UnusedRepo(),
        email_log_repo=_UnusedRepo(),
    )
    matching = MatchingResult(
        match_percentage=77.0,
        missing_skills=["Docker"],
        extra_skills=["Redis"],
        experience_comparison="Meets the backend bar.",
        explanation="Python and Django are evidenced by the billing project.",
    )
    final_state = {
        "matching_result": matching,
        "score_result": ScoringResult(
            breakdown=ScoreBreakdown(
                skills_score=80,
                experience_score=70,
                projects_score=75,
                education_score=60,
                certifications_score=40,
            ),
            total_score=74,
            reasoning="Weighted toward skills.",
        ),
        "decision": DecisionResult(decision=DecisionType.MANUAL_REVIEW, reason="One required skill is missing."),
    }

    await service._persist_results(candidate, final_state)

    assert candidate.matching_result["missing_skills"] == ["Docker"]
    assert candidate.matching_result["explanation"].startswith("Python and Django")
    assert candidate.match_percentage == 77.0
    assert candidate.status == CandidateStatus.MANUAL_REVIEW
    assert scores.rows[0].total_score == 74
