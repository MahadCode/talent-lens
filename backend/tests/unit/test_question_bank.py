"""Tests for generating, editing, and deleting a saved interview question set."""

from __future__ import annotations

import uuid

import pytest

from app.exceptions.errors import ValidationAppError
from app.models.candidate import Candidate
from app.models.job import Job
from app.core.constants import CandidateStatus, JobStatus
from app.schemas.interview import QuestionUpdate
from app.services.interview_service import InterviewService
from tests.fakes import MemoryCandidateRepo, MemoryInterviewRepo, MemoryJobRepo


def _valid_set(*_args) -> list[dict]:
    return [
        {"question": "What is a view?", "focus_area": "Django", "difficulty": "beginner", "guideline": "Expect a short definition."},
        {"question": "How do you index a table?", "focus_area": "PostgreSQL", "difficulty": "intermediate", "guideline": "Look for tradeoffs."},
        {"question": "Design a migration rollback.", "focus_area": "PostgreSQL", "difficulty": "advanced", "guideline": "Look for a safe plan."},
        {"question": "Walk through the billing API.", "focus_area": "project", "difficulty": "intermediate", "guideline": "Tie the answer to the resume project."},
    ]


def _service(generator=_valid_set):
    candidates = MemoryCandidateRepo()
    jobs = MemoryJobRepo()
    interviews = MemoryInterviewRepo()
    service = InterviewService(
        candidate_repo=candidates,
        interview_repo=interviews,
        job_repo=jobs,
        question_generator=generator,
    )
    return service, candidates, jobs, interviews


async def _seed():
    service, candidates, jobs, interviews = _service()
    job = Job(
        title="Backend Developer",
        description="Build APIs",
        requirements="Python, Django, PostgreSQL, Docker",
        status=JobStatus.OPEN,
        created_by_id=uuid.uuid4(),
    )
    await jobs.add(job)
    candidate = Candidate(
        job_id=job.id,
        status=CandidateStatus.PARSED,
        score_overridden=False,
        parsed_profile={"skills": ["Python", "Django"], "projects": ["Billing API"]},
    )
    await candidates.add(candidate)
    return service, candidate, interviews


async def test_generate_edit_delete_and_regenerate() -> None:
    service, candidate, _ = await _seed()

    created = await service.generate_question_set(candidate.id)
    assert {item.difficulty for item in created.questions} == {"beginner", "intermediate", "advanced"}
    assert any(item.focus_area == "project" for item in created.questions)

    target = created.questions[0]
    edited = await service.update_question(target.id, QuestionUpdate(question="What is a Django view?"))
    assert edited.question == "What is a Django view?"

    remaining = await service.delete_question(target.id)
    assert all(item.id != target.id for item in remaining.questions)
    assert remaining.interview_id == created.interview_id

    regenerated = await service.generate_question_set(candidate.id)
    assert regenerated.interview_id == created.interview_id
    assert {item.id for item in regenerated.questions}.isdisjoint({item.id for item in created.questions})


async def test_incomplete_question_set_is_rejected() -> None:
    service, candidates, jobs, _ = _service(generator=lambda *_args: _valid_set()[:2])
    job = Job(
        title="Backend Developer",
        description="Build APIs",
        requirements="Python",
        status=JobStatus.OPEN,
        created_by_id=uuid.uuid4(),
    )
    await jobs.add(job)
    candidate = Candidate(
        job_id=job.id,
        status=CandidateStatus.PARSED,
        score_overridden=False,
        parsed_profile={"skills": ["Python"], "projects": []},
    )
    await candidates.add(candidate)

    with pytest.raises(ValidationAppError):
        await service.generate_question_set(candidate.id)


async def test_empty_question_edit_is_rejected() -> None:
    service, candidate, _ = await _seed()
    created = await service.generate_question_set(candidate.id)

    with pytest.raises(ValidationAppError):
        await service.update_question(created.questions[0].id, QuestionUpdate())
