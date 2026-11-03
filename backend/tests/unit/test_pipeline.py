"""Tests for assessment reads, status changes, notes, profile corrections, and score overrides."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.core.constants import CandidateStatus
from app.exceptions.errors import NotFoundError, ValidationAppError
from app.models.candidate import Candidate
from app.models.score import Score
from app.schemas.candidate import CandidateProfileUpdate, CandidateRead
from app.services.candidate_service import CandidateService
from app.services.pipeline_rules import assert_transition
from tests.fakes import MemoryCandidateRepo, MemoryEventRepo, MemoryNoteRepo, MemoryScoreRepo


def _service() -> tuple[CandidateService, MemoryCandidateRepo, MemoryScoreRepo, MemoryNoteRepo, MemoryEventRepo]:
    candidates = MemoryCandidateRepo()
    scores = MemoryScoreRepo()
    notes = MemoryNoteRepo()
    events = MemoryEventRepo(candidates)
    service = CandidateService(
        candidate_repo=candidates, score_repo=scores, note_repo=notes, event_repo=events
    )
    return service, candidates, scores, notes, events


def _candidate(**overrides) -> Candidate:
    values = {
        "job_id": uuid.uuid4(),
        "status": CandidateStatus.PARSED,
        "score_overridden": False,
        "parsed_profile": {"skills": ["Python"], "projects": ["Billing API"]},
        "matching_result": {
            "match_percentage": 80.0,
            "missing_skills": ["Docker"],
            "extra_skills": ["Redis"],
            "experience_comparison": "Enough backend experience.",
            "explanation": "Strong Python evidence in the billing project.",
        },
        "match_percentage": 80.0,
    }
    values.update(overrides)
    candidate = Candidate(**values)
    candidate.id = uuid.uuid4()
    candidate.created_at = datetime.now(timezone.utc)
    candidate.updated_at = candidate.created_at
    return candidate


def _score(candidate_id: uuid.UUID) -> Score:
    score = Score(
        candidate_id=candidate_id,
        skills_score=90,
        experience_score=70,
        projects_score=80,
        education_score=60,
        certifications_score=50,
        total_score=81,
        reasoning="Skills carry the most weight.",
    )
    score.id = uuid.uuid4()
    score.created_at = datetime.now(timezone.utc)
    score.updated_at = score.created_at
    return score


def test_illegal_jump_from_new_is_rejected() -> None:
    with pytest.raises(ValidationAppError):
        assert_transition(CandidateStatus.NEW, CandidateStatus.SHORTLISTED)


def test_candidate_read_does_not_expose_notes() -> None:
    assert "notes" not in CandidateRead.model_fields
    assert "body" not in CandidateRead.model_fields


async def test_assessment_is_missing_until_a_score_exists() -> None:
    service, candidates, _, _, _ = _service()
    candidate = _candidate()
    await candidates.add(candidate)

    with pytest.raises(NotFoundError):
        await service.get_assessment(candidate.id)


async def test_assessment_returns_stored_evidence() -> None:
    service, candidates, scores, _, _ = _service()
    candidate = _candidate()
    await candidates.add(candidate)
    await scores.add(_score(candidate.id))

    assessment = await service.get_assessment(candidate.id)

    assert assessment.total_score == 81
    assert assessment.missing_skills == ["Docker"]
    assert assessment.explanation == "Strong Python evidence in the billing project."
    assert assessment.score_overridden is False


async def test_shortlist_then_reject_writes_two_events() -> None:
    service, candidates, _, _, events = _service()
    candidate = _candidate()
    await candidates.add(candidate)
    actor = uuid.uuid4()

    await service.change_status(candidate.id, CandidateStatus.SHORTLISTED, actor)
    await service.change_status(candidate.id, CandidateStatus.REJECTED, actor)

    history = await service.list_events(candidate.id)
    assert [event.to_status for event in history] == [
        CandidateStatus.SHORTLISTED,
        CandidateStatus.REJECTED,
    ]
    assert history[0].actor_id == actor
    assert history[0].from_status == CandidateStatus.PARSED
    assert len(events.rows) == 2


async def test_note_is_private_and_listed_newest_first() -> None:
    service, candidates, _, _, _ = _service()
    candidate = _candidate()
    await candidates.add(candidate)
    author = uuid.uuid4()

    await service.add_note(candidate.id, author, "First")
    await service.add_note(candidate.id, author, "Second")

    listed = await service.list_notes(candidate.id)
    public = CandidateRead.model_validate(candidate)

    assert [note.body for note in listed] == ["Second", "First"]
    assert public.model_dump().get("notes") is None


async def test_profile_correction_clears_the_match_explanation() -> None:
    service, candidates, _, _, _ = _service()
    candidate = _candidate()
    await candidates.add(candidate)

    updated = await service.update_profile(
        candidate.id, CandidateProfileUpdate(skills=["Python", "Django"])
    )

    assert updated.parsed_profile["skills"] == ["Python", "Django"]
    assert updated.parsed_profile["projects"] == ["Billing API"]
    assert updated.matching_result is None


async def test_score_override_flags_the_candidate_and_stores_the_reason() -> None:
    service, candidates, scores, _, _ = _service()
    candidate = _candidate()
    await candidates.add(candidate)
    await scores.add(_score(candidate.id))
    actor = uuid.uuid4()

    updated = await service.override_score(candidate.id, 72, "Portfolio was stronger than the resume.", actor)

    assert updated.score_overridden is True
    assert scores.rows[0].total_score == 72
    notes = await service.list_notes(candidate.id)
    assert "72" in notes[0].body
    assert "Portfolio was stronger" in notes[0].body
