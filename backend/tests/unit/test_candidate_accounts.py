"""Tests for candidate accounts: apply, own applications, and recruiter-data isolation."""

from __future__ import annotations

import uuid

import pytest

from ai_agents.utils.schemas import ParsedCandidate
from app.core.constants import CandidateStatus, HR_ROLES, INTERVIEW_ROLES, JobStatus, UserRole
from app.exceptions.errors import ConflictError, NotFoundError
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.schemas.candidate import CandidateApplicationRead, CandidateProfileUpdate
from app.services.candidate_service import CandidateService
from app.services.job_service import JobService
from app.services.resume_service import ResumeService
from tests.fakes import MemoryCandidateRepo, MemoryJobRepo, MemoryResumeRepo


class FakeParser:
    """Returns a fixed parsed resume so tests do not call Gemini."""

    def run(self, resume_text: str) -> ParsedCandidate:
        return ParsedCandidate(
            name="Ada Lovelace",
            email="ada@example.com",
            skills=["Python", "Django"],
            experience=["Backend engineer"],
            education=["Mathematics"],
            projects=["Analytical Engine"],
            certifications=[],
            github=None,
            linkedin=None,
        )


def _user(role: UserRole = UserRole.CANDIDATE) -> User:
    user = User(
        full_name="Ada Lovelace",
        email="ada@example.com",
        hashed_password="hashed",
        role=role,
    )
    user.id = uuid.uuid4()
    return user


def _job(status: JobStatus = JobStatus.OPEN) -> Job:
    job = Job(
        title="Backend Developer",
        description="Build APIs",
        requirements="Python, Django, PostgreSQL, Docker",
        status=status,
        created_by_id=uuid.uuid4(),
    )
    job.id = uuid.uuid4()
    return job


def _resume_service():
    candidates = MemoryCandidateRepo()
    jobs = MemoryJobRepo()
    resumes = MemoryResumeRepo()
    service = ResumeService(
        resume_repo=resumes,
        candidate_repo=candidates,
        job_repo=jobs,
        parser_agent=FakeParser(),
    )
    service._persist_file = lambda *args, **kwargs: "/tmp/resume.pdf"
    return service, candidates, jobs, resumes


def test_candidate_role_cannot_use_staff_sets() -> None:
    assert UserRole.CANDIDATE not in HR_ROLES
    assert UserRole.CANDIDATE not in INTERVIEW_ROLES


def test_candidate_payload_omits_recruiter_fields() -> None:
    assert "notes" not in CandidateApplicationRead.model_fields
    assert "match_percentage" not in CandidateApplicationRead.model_fields
    assert "matching_result" not in CandidateApplicationRead.model_fields
    assert "score_overridden" not in CandidateApplicationRead.model_fields


async def test_open_jobs_hide_drafts_from_candidates() -> None:
    jobs = MemoryJobRepo()
    service = JobService(job_repo=jobs)
    open_job = _job(JobStatus.OPEN)
    draft = _job(JobStatus.DRAFT)
    await jobs.add(open_job)
    await jobs.add(draft)
    candidate = _user()

    listed = await service.list_open_jobs()
    visible = await service.get_job_for_viewer(open_job.id, candidate)

    assert [job.id for job in listed] == [open_job.id]
    assert visible.id == open_job.id
    with pytest.raises(NotFoundError):
        await service.get_job_for_viewer(draft.id, candidate)


async def test_hr_can_read_a_draft_job() -> None:
    jobs = MemoryJobRepo()
    service = JobService(job_repo=jobs)
    draft = _job(JobStatus.DRAFT)
    await jobs.add(draft)

    visible = await service.get_job_for_viewer(draft.id, _user(UserRole.RECRUITER))
    assert visible.id == draft.id


async def test_candidate_can_apply_to_an_open_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.resume_service.extract_text_from_pdf", lambda _bytes: "Ada Python Django")
    service, candidates, jobs, resumes = _resume_service()
    job = _job()
    await jobs.add(job)
    user = _user()

    resume, candidate, parsed = await service.apply_as_candidate(user, job.id, "ada.pdf", b"%PDF-1.4")

    assert candidate.user_id == user.id
    assert candidate.job_id == job.id
    assert candidate.status == CandidateStatus.PARSED
    assert parsed.skills == ["Python", "Django"]
    assert candidate.parsed_profile["projects"] == ["Analytical Engine"]
    assert resume.original_filename == "ada.pdf"
    assert len(resumes.rows) == 1
    assert candidates.rows[candidate.id].email == "ada@example.com"


async def test_duplicate_apply_and_closed_job_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.resume_service.extract_text_from_pdf", lambda _bytes: "text")
    service, _, jobs, _ = _resume_service()
    open_job = _job()
    closed = _job(JobStatus.CLOSED)
    await jobs.add(open_job)
    await jobs.add(closed)
    user = _user()

    await service.apply_as_candidate(user, open_job.id, "ada.pdf", b"%PDF")
    with pytest.raises(ConflictError):
        await service.apply_as_candidate(user, open_job.id, "ada.pdf", b"%PDF")
    with pytest.raises(NotFoundError):
        await service.apply_as_candidate(user, closed.id, "ada.pdf", b"%PDF")
    with pytest.raises(NotFoundError):
        await service.apply_as_candidate(user, uuid.uuid4(), "ada.pdf", b"%PDF")


async def test_list_mine_is_scoped_and_hides_other_people() -> None:
    candidates = MemoryCandidateRepo()
    jobs = MemoryJobRepo()
    service = CandidateService(candidate_repo=candidates, job_repo=jobs)
    job = _job()
    await jobs.add(job)
    owner = uuid.uuid4()
    mine = Candidate(
        job_id=job.id,
        user_id=owner,
        status=CandidateStatus.PARSED,
        score_overridden=False,
        parsed_profile={"skills": ["Python"]},
        matching_result={"missing_skills": ["Docker"], "explanation": "secret"},
        match_percentage=88.0,
    )
    other = Candidate(
        job_id=job.id,
        user_id=uuid.uuid4(),
        status=CandidateStatus.SHORTLISTED,
        score_overridden=False,
        parsed_profile={"skills": ["Go"]},
    )
    await candidates.add(mine)
    await candidates.add(other)

    listed = await service.list_mine(owner)
    dumped = listed[0].model_dump()

    assert [row.id for row in listed] == [mine.id]
    assert listed[0].job_title == "Backend Developer"
    assert listed[0].status == CandidateStatus.PARSED
    assert "notes" not in dumped
    assert "match_percentage" not in dumped
    assert "matching_result" not in dumped
    with pytest.raises(NotFoundError):
        await service.get_owned(other.id, owner)


async def test_candidate_can_correct_own_resume_only() -> None:
    candidates = MemoryCandidateRepo()
    jobs = MemoryJobRepo()
    service = CandidateService(candidate_repo=candidates, job_repo=jobs)
    job = _job()
    await jobs.add(job)
    owner = uuid.uuid4()
    mine = Candidate(
        job_id=job.id,
        user_id=owner,
        status=CandidateStatus.PARSED,
        score_overridden=False,
        parsed_profile={"skills": ["Python"], "projects": ["Billing API"]},
        matching_result={"explanation": "stale"},
    )
    other = Candidate(
        job_id=job.id,
        user_id=uuid.uuid4(),
        status=CandidateStatus.PARSED,
        score_overridden=False,
        parsed_profile={"skills": ["Go"]},
    )
    await candidates.add(mine)
    await candidates.add(other)

    updated = await service.update_own_profile(
        mine.id, owner, CandidateProfileUpdate(skills=["Python", "Django"])
    )
    payload = await service.get_own_application(mine.id, owner)

    assert updated.parsed_profile["skills"] == ["Python", "Django"]
    assert updated.matching_result is None
    assert payload.parsed_profile["skills"] == ["Python", "Django"]
    with pytest.raises(NotFoundError):
        await service.update_own_profile(other.id, owner, CandidateProfileUpdate(skills=["Rust"]))


async def test_resume_me_returns_owned_parse_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.resume_service.extract_text_from_pdf", lambda _bytes: "text")
    service, candidates, jobs, _ = _resume_service()
    job = _job()
    await jobs.add(job)
    user = _user()
    other = Candidate(
        job_id=job.id,
        user_id=uuid.uuid4(),
        status=CandidateStatus.PARSED,
        score_overridden=False,
        parsed_profile={"skills": ["secret"]},
    )
    await candidates.add(other)
    resume, candidate, _parsed = await service.apply_as_candidate(user, job.id, "ada.pdf", b"%PDF")

    latest, owned = await service.get_resume_for_owner(user.id)
    specific, _ = await service.get_resume_for_owner(user.id, candidate.id)

    assert latest.id == resume.id
    assert owned.id == candidate.id
    assert specific.id == resume.id
    with pytest.raises(NotFoundError):
        await service.get_resume_for_owner(user.id, other.id)
    with pytest.raises(NotFoundError):
        await service.get_resume_for_owner(uuid.uuid4())
