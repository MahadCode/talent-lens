"""Business logic for interview question generation and evaluation.

Question generation reuses `InterviewAgent.next_question` directly, as
specified. Transcript evaluation has no dedicated agent in the AI layer
(only one-question-at-a-time generation exists there), so this service
adds a thin, separately-defined evaluation step using the same shared
Gemini client and the `InterviewResult` schema already defined in the
agent layer's `utils.schemas` module — no agent or graph logic is
duplicated or regenerated.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from pydantic import BaseModel, Field

from ai_agents.agents.interview_agent import InterviewAgent
from ai_agents.config.llm import get_gemini_llm
from ai_agents.utils.schemas import InterviewResult
from app.core.constants import QuestionDifficulty
from app.exceptions.errors import NotFoundError, ValidationAppError
from app.models.candidate import Candidate
from app.models.interview import Interview
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.interview_repository import InterviewRepository
from app.repositories.job_repository import JobRepository
from app.schemas.interview import InterviewQuestionResponse, QuestionSetRead, QuestionUpdate, StoredQuestionRead

_EVALUATION_SYSTEM_PROMPT: str = """You are an expert technical interviewer reviewing a completed
interview transcript.

Given the full list of questions and answers, assess the candidate's overall performance and
decide whether they passed. Return ONLY the structured output described by the response schema.
"""

_QUESTION_SET_PROMPT = """You write interview questions for a recruiter.
Return exactly four questions:
- one beginner
- one intermediate
- one advanced
- one question about a project the candidate actually listed
Each question needs a short answer guideline the interviewer can use.
Set focus_area to "project" on the project question.
Do not invent projects that were not provided.
"""


class _GeneratedQuestion(BaseModel):
    """One question returned by the question-set model."""

    question: str
    focus_area: str
    difficulty: str
    guideline: str


class _GeneratedQuestionSet(BaseModel):
    """The full set returned by the question-set model."""

    questions: list[_GeneratedQuestion] = Field(default_factory=list)


def _default_question_set(job_description: str, skills: list[str], projects: list[str]) -> list[dict]:
    """Generate a question set with the shared Gemini client.

    Args:
        job_description: Job title, description, and requirements.
        skills: Skills parsed from the resume.
        projects: Projects parsed from the resume.

    Returns:
        Raw question dicts before ids are assigned.
    """

    llm = get_gemini_llm()
    structured_llm = llm.with_structured_output(_GeneratedQuestionSet)
    result = structured_llm.invoke(
        [
            ("system", _QUESTION_SET_PROMPT),
            (
                "human",
                "Job:\n"
                f"{job_description}\n\n"
                f"Skills: {', '.join(skills) or 'none listed'}\n"
                f"Projects: {', '.join(projects) or 'none listed'}",
            ),
        ]
    )
    return [item.model_dump() for item in result.questions]


class InterviewService:
    """Coordinates adaptive question generation and transcript evaluation."""

    def __init__(
        self,
        candidate_repo: CandidateRepository,
        interview_repo: InterviewRepository,
        job_repo: JobRepository | None = None,
        interview_agent: InterviewAgent | None = None,
        question_generator: Callable[[str, list[str], list[str]], list[dict]] | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            candidate_repo: Repository for `Candidate` persistence.
            interview_repo: Repository for `Interview` persistence.
            job_repo: Repository for `Job` persistence. Required for question sets.
            interview_agent: Optional agent override, primarily for testing.
            question_generator: Optional replacement for the LLM question-set
                call. Receives job text, skills, and projects.
        """

        self._candidate_repo = candidate_repo
        self._interview_repo = interview_repo
        self._job_repo = job_repo
        self._interview_agent = interview_agent or InterviewAgent()
        self._question_generator = question_generator or _default_question_set

    async def next_question(
        self, candidate_id: uuid.UUID, job_description: str, conversation_history: list[str]
    ) -> InterviewQuestionResponse:
        """Generate the next adaptive interview question for a candidate.

        Args:
            candidate_id: The candidate being interviewed.
            job_description: The job description to ground the question in.
            conversation_history: Prior Q&A turns, oldest first.

        Returns:
            The next question to ask, as an `InterviewQuestionResponse`.

        Raises:
            NotFoundError: If the candidate does not exist or has not been parsed.
        """

        candidate = await self._get_parsed_candidate(candidate_id)
        skills = list((candidate.parsed_profile or {}).get("skills") or [])
        weaknesses = list((candidate.parsed_profile or {}).get("missing_skills") or [])

        question = self._interview_agent.next_question(
            job_description=job_description,
            candidate_skills=skills,
            candidate_weaknesses=weaknesses,
            conversation_history=conversation_history,
        )
        return InterviewQuestionResponse(
            question=question.question,
            focus_area=question.focus_area,
            is_follow_up=question.is_follow_up,
        )

    async def evaluate_transcript(self, candidate_id: uuid.UUID, questions_and_answers: list[str]) -> Interview:
        """Evaluate a completed interview transcript and persist the result.

        Args:
            candidate_id: The candidate whose interview is being evaluated.
            questions_and_answers: The full Q&A transcript, as strings.

        Returns:
            The persisted `Interview` record.

        Raises:
            NotFoundError: If the candidate does not exist.
        """

        candidate = await self._candidate_repo.get_by_id(candidate_id)
        if candidate is None:
            raise NotFoundError("Candidate not found.")

        result = self._run_evaluation(questions_and_answers)

        interview = Interview(
            candidate_id=candidate.id,
            questions=None,
            overall_assessment=result.overall_assessment,
            passed=result.passed,
        )
        return await self._interview_repo.add(interview)

    def _run_evaluation(self, questions_and_answers: list[str]) -> InterviewResult:
        """Invoke the shared LLM to evaluate a transcript against `InterviewResult`.

        Args:
            questions_and_answers: The full Q&A transcript, as strings.

        Returns:
            A validated `InterviewResult`.
        """

        llm = get_gemini_llm()
        structured_llm = llm.with_structured_output(InterviewResult)
        transcript = "\n".join(questions_and_answers)
        return structured_llm.invoke(
            [
                ("system", _EVALUATION_SYSTEM_PROMPT),
                ("human", f"Interview transcript:\n---\n{transcript}\n---\n\nEvaluate this interview."),
            ]
        )

    async def _get_parsed_candidate(self, candidate_id: uuid.UUID) -> Candidate:
        """Fetch a candidate and ensure it has been parsed.

        Args:
            candidate_id: The candidate's id.

        Returns:
            The matching, parsed `Candidate`.

        Raises:
            NotFoundError: If the candidate does not exist or lacks a
                parsed profile.
        """

        candidate = await self._candidate_repo.get_by_id(candidate_id)
        if candidate is None:
            raise NotFoundError("Candidate not found.")
        if candidate.parsed_profile is None:
            raise NotFoundError("Candidate has not been parsed yet.")
        return candidate

    async def generate_question_set(self, candidate_id: uuid.UUID) -> QuestionSetRead:
        """Create or replace the saved interview question set for a candidate.

        Args:
            candidate_id: The candidate to write questions for.

        Returns:
            The saved question set.

        Raises:
            NotFoundError: If the candidate is missing, unparsed, or has no job.
            ValidationAppError: If the generated set is missing a required question.
        """

        candidate = await self._get_parsed_candidate(candidate_id)
        if self._job_repo is None:
            raise NotFoundError("Job associated with this candidate no longer exists.")
        job = await self._job_repo.get_by_id(candidate.job_id)
        if job is None:
            raise NotFoundError("Job associated with this candidate no longer exists.")

        profile = candidate.parsed_profile or {}
        raw_questions = self._question_generator(
            f"{job.title}\n{job.description}\n{job.requirements}",
            list(profile.get("skills") or []),
            list(profile.get("projects") or []),
        )
        questions = [_normalize_question(item) for item in raw_questions]
        _validate_question_set(questions)

        bank = await self._interview_repo.get_question_bank(candidate_id)
        if bank is None:
            bank = await self._interview_repo.add(
                Interview(candidate_id=candidate.id, questions=questions, overall_assessment=None, passed=None)
            )
        else:
            bank.questions = questions
        return _question_set_read(candidate.id, bank)

    async def list_questions(self, candidate_id: uuid.UUID) -> QuestionSetRead:
        """Return the saved question set, or an empty set if none exists.

        Args:
            candidate_id: The candidate whose questions to read.

        Returns:
            The saved set. `interview_id` is null when nothing has been generated.

        Raises:
            NotFoundError: If the candidate does not exist.
        """

        candidate = await self._candidate_repo.get_by_id(candidate_id)
        if candidate is None:
            raise NotFoundError("Candidate not found.")
        bank = await self._interview_repo.get_question_bank(candidate_id)
        if bank is None:
            return QuestionSetRead(candidate_id=candidate.id, interview_id=None, questions=[])
        return _question_set_read(candidate.id, bank)

    async def update_question(self, question_id: uuid.UUID, data: QuestionUpdate) -> StoredQuestionRead:
        """Edit one saved question.

        Args:
            question_id: The id stored inside the question JSON.
            data: Fields to change.

        Returns:
            The edited question.

        Raises:
            NotFoundError: If no saved question has this id.
            ValidationAppError: If the body changes nothing, or difficulty is unknown.
        """

        changes = data.model_dump(exclude_unset=True)
        if not changes:
            raise ValidationAppError("Provide at least one field to update.")
        if "difficulty" in changes:
            changes["difficulty"] = _parse_difficulty(changes["difficulty"])

        interview = await self._interview_repo.find_by_question_id(str(question_id))
        if interview is None or not interview.questions:
            raise NotFoundError("Question not found.")

        questions = [dict(item) for item in interview.questions]
        for item in questions:
            if item.get("id") == str(question_id):
                item.update(changes)
                interview.questions = questions
                return StoredQuestionRead.model_validate(item)
        raise NotFoundError("Question not found.")

    async def delete_question(self, question_id: uuid.UUID) -> QuestionSetRead:
        """Remove one saved question.

        Args:
            question_id: The id stored inside the question JSON.

        Returns:
            The question set that remains.

        Raises:
            NotFoundError: If no saved question has this id.
        """

        interview = await self._interview_repo.find_by_question_id(str(question_id))
        if interview is None or not interview.questions:
            raise NotFoundError("Question not found.")

        questions = [dict(item) for item in interview.questions if item.get("id") != str(question_id)]
        if len(questions) == len(interview.questions):
            raise NotFoundError("Question not found.")
        interview.questions = questions
        return _question_set_read(interview.candidate_id, interview)


def _parse_difficulty(value: str) -> str:
    """Validate a difficulty label.

    Args:
        value: The raw difficulty string.

    Returns:
        The normalized difficulty value.

    Raises:
        ValidationAppError: If the label is not beginner, intermediate, or advanced.
    """

    try:
        return QuestionDifficulty(str(value).lower()).value
    except ValueError as exc:
        raise ValidationAppError("Difficulty must be beginner, intermediate, or advanced.") from exc


def _normalize_question(item: dict) -> dict:
    """Assign an id and validate one generated question.

    Args:
        item: A raw question dict from the generator.

    Returns:
        A stored question dict.

    Raises:
        ValidationAppError: If a required field is missing or difficulty is unknown.
    """

    try:
        question = str(item["question"])
        focus_area = str(item["focus_area"])
        difficulty = _parse_difficulty(str(item["difficulty"]))
        guideline = str(item["guideline"])
    except KeyError as exc:
        raise ValidationAppError("Generated question is missing a required field.") from exc
    return {
        "id": str(uuid.uuid4()),
        "question": question,
        "focus_area": focus_area,
        "difficulty": difficulty,
        "guideline": guideline,
        "is_follow_up": bool(item.get("is_follow_up", False)),
    }


def _validate_question_set(questions: list[dict]) -> None:
    """Require beginner, intermediate, advanced, and a project question.

    Args:
        questions: Normalized question dicts.

    Raises:
        ValidationAppError: If any required kind of question is missing.
    """

    difficulties = {item["difficulty"] for item in questions}
    required = {level.value for level in QuestionDifficulty}
    has_project = any("project" in item["focus_area"].casefold() for item in questions)
    if not required.issubset(difficulties) or not has_project:
        raise ValidationAppError(
            "Question set must include beginner, intermediate, advanced, and a project question."
        )


def _question_set_read(candidate_id: uuid.UUID, interview: Interview) -> QuestionSetRead:
    """Build the API representation of a stored question set.

    Args:
        candidate_id: The candidate the set belongs to.
        interview: The interview row holding the questions.

    Returns:
        A `QuestionSetRead` payload.
    """

    return QuestionSetRead(
        candidate_id=candidate_id,
        interview_id=interview.id,
        questions=[StoredQuestionRead.model_validate(item) for item in (interview.questions or [])],
    )
