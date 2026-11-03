"""Tests for saving or previewing extracted job requirements."""

from __future__ import annotations

import uuid

from app.core.constants import JobStatus
from app.models.job import Job
from app.services.job_service import JobService
from tests.fakes import MemoryJobRepo


def _extracted(description: str, requirements: str) -> dict:
    return {
        "required_skills": ["Python", "Django"],
        "preferred_skills": ["Docker"],
        "experience": "3 years",
        "qualifications": ["Bachelor's degree"],
    }


async def test_extract_can_preview_without_saving() -> None:
    jobs = MemoryJobRepo()
    service = JobService(job_repo=jobs, extractor=_extracted)
    job = await jobs.add(
        Job(
            title="Backend Developer",
            description="Python services",
            requirements="Django and PostgreSQL",
            status=JobStatus.OPEN,
            created_by_id=uuid.uuid4(),
        )
    )

    payload, applied = await service.extract_requirements(job.id, apply=False)

    assert applied is False
    assert payload["required_skills"] == ["Python", "Django"]
    assert job.extracted_requirements is None


async def test_extract_apply_saves_on_the_job() -> None:
    jobs = MemoryJobRepo()
    service = JobService(job_repo=jobs, extractor=_extracted)
    job = await jobs.add(
        Job(
            title="Backend Developer",
            description="Python services",
            requirements="Django and PostgreSQL",
            status=JobStatus.OPEN,
            created_by_id=uuid.uuid4(),
        )
    )

    payload, applied = await service.extract_requirements(job.id, apply=True)

    assert applied is True
    assert job.extracted_requirements == payload
