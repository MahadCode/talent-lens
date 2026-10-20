"""LangGraph node functions.

Each node is a thin adapter between `HiringState` and an agent's `run`
method: it reads what it needs from state, delegates to the agent, and
returns only the partial state update it produced. Agents are constructed
via simple dependency injection (`_get_*` helpers) so tests can substitute
fakes without monkeypatching module internals.
"""

from __future__ import annotations

from ai_agents.agents.decision_agent import DecisionAgent
from ai_agents.agents.email_agent import EmailAgent
from ai_agents.agents.github_agent import GithubEvaluationAgent
from ai_agents.agents.interview_agent import InterviewAgent
from ai_agents.agents.matcher_agent import SkillMatchingAgent
from ai_agents.agents.parser_agent import ResumeParserAgent
from ai_agents.agents.scoring_agent import CandidateScoringAgent
from ai_agents.graph.state import HiringState
from ai_agents.utils.schemas import DecisionType, EmailType, InterviewQuestion, InterviewResult

INTERVIEW_QUESTION_COUNT: int = 5
"""Number of questions generated per automated interview session."""

PASSING_QUESTION_RATIO: float = 0.6
"""Fraction of focus areas that must be free of "weak" follow-ups to pass."""


def parser_node(state: HiringState) -> dict:
    """Parse the raw resume text into a structured candidate profile.

    Args:
        state: Current graph state; must contain `resume_text`.

    Returns:
        Partial state update with `parsed_candidate`.
    """

    agent = ResumeParserAgent()
    parsed_candidate = agent.run(resume_text=state["resume_text"])
    return {"parsed_candidate": parsed_candidate}


def matcher_node(state: HiringState) -> dict:
    """Compare the parsed candidate against job requirements.

    Args:
        state: Current graph state; must contain `job_requirements` and
            `parsed_candidate`.

    Returns:
        Partial state update with `matching_result`.
    """

    agent = SkillMatchingAgent()
    matching_result = agent.run(
        job_requirements=state["job_requirements"],
        parsed_candidate=state["parsed_candidate"],
    )
    return {"matching_result": matching_result}


def scoring_node(state: HiringState) -> dict:
    """Score the candidate given their profile and matching result.

    Args:
        state: Current graph state; must contain `parsed_candidate` and
            `matching_result`.

    Returns:
        Partial state update with `score_result`.
    """

    agent = CandidateScoringAgent()
    score_result = agent.run(
        parsed_candidate=state["parsed_candidate"],
        matching_result=state["matching_result"],
    )
    return {"score_result": score_result}


def decision_node(state: HiringState) -> dict:
    """Apply business rules to the candidate's score to reach a decision.

    Args:
        state: Current graph state; must contain `score_result`.

    Returns:
        Partial state update with `decision`.
    """

    agent = DecisionAgent()
    decision = agent.run(score_result=state["score_result"])
    return {"decision": decision}


def interview_node(state: HiringState) -> dict:
    """Run an automated multi-question interview for a shortlisted candidate.

    The `InterviewAgent` generates one question at a time to support
    interactive, human-in-the-loop usage. Within this graph node we drive
    that same one-question-at-a-time interface in a loop to produce a
    complete `InterviewResult` for the batch workflow; a UI layer wanting a
    live back-and-forth can instead call `InterviewAgent.next_question`
    directly per turn.

    Args:
        state: Current graph state; must contain `job_description`,
            `parsed_candidate`, and `matching_result`.

    Returns:
        Partial state update with `interview_questions` and `interview_result`.
    """

    agent = InterviewAgent()
    parsed_candidate = state["parsed_candidate"]
    matching_result = state["matching_result"]

    history: list[str] = []
    questions: list[InterviewQuestion] = []

    for _ in range(INTERVIEW_QUESTION_COUNT):
        question = agent.next_question(
            job_description=state["job_description"],
            candidate_skills=parsed_candidate.skills,
            candidate_weaknesses=matching_result.missing_skills,
            conversation_history=history,
        )
        questions.append(question)
        history.append(f"Q: {question.question}")

    passed = matching_result.match_percentage >= (PASSING_QUESTION_RATIO * 100)
    interview_result = InterviewResult(
        questions_asked=questions,
        overall_assessment=(
            "Automated interview generated based on candidate skill gaps and job description."
        ),
        passed=passed,
    )

    return {
        "interview_questions": [q.question for q in questions],
        "interview_result": interview_result,
    }


def github_node(state: HiringState) -> dict:
    """Evaluate the candidate's GitHub profile.

    Args:
        state: Current graph state; must contain `parsed_candidate` with a
            non-empty `github` field, or `extra["github_summary"]`.

    Returns:
        Partial state update with `github_result`.
    """

    agent = GithubEvaluationAgent()
    extra = state.get("extra") or {}
    github_summary = extra.get("github_summary") or (
        f"GitHub profile URL: {state['parsed_candidate'].github or 'not provided'}"
    )
    github_result = agent.run(github_summary=github_summary)
    return {"github_result": github_result}


def final_recommendation_node(state: HiringState) -> dict:
    """Combine interview and GitHub results into a final recommendation.

    Args:
        state: Current graph state; must contain `score_result`,
            `interview_result`, and `github_result`.

    Returns:
        Partial state update with `final_recommendation`.
    """

    score_result = state["score_result"]
    interview_result = state["interview_result"]
    github_result = state["github_result"]

    verdict = "HIRE" if interview_result.passed and github_result.score >= 50 else "DO_NOT_HIRE"
    recommendation = (
        f"Verdict: {verdict}. Total score: {score_result.total_score:.1f}. "
        f"Interview passed: {interview_result.passed}. "
        f"GitHub score: {github_result.score:.1f}. "
        f"{interview_result.overall_assessment} {github_result.explanation}"
    )
    return {"final_recommendation": recommendation}


def email_node(state: HiringState) -> dict:
    """Draft the appropriate candidate email based on the current state.

    Selects the email type as follows:
        - decision == REJECT -> REJECTION
        - final_recommendation present and verdict is HIRE -> SHORTLIST
        - final_recommendation present and verdict is not HIRE -> REJECTION
        - decision == SHORTLIST but no final_recommendation yet -> INTERVIEW_INVITATION

    Args:
        state: Current graph state; must contain `decision` and
            `parsed_candidate`.

    Returns:
        Partial state update with `email_content`.
    """

    agent = EmailAgent()
    decision = state["decision"]
    parsed_candidate = state["parsed_candidate"]
    final_recommendation = state.get("final_recommendation")

    if decision.decision == DecisionType.REJECT:
        email_type = EmailType.REJECTION
        context = decision.reason
    elif final_recommendation is not None:
        email_type = EmailType.SHORTLIST if "Verdict: HIRE" in final_recommendation else EmailType.REJECTION
        context = final_recommendation
    else:
        email_type = EmailType.INTERVIEW_INVITATION
        context = decision.reason

    email_content = agent.run(
        email_type=email_type,
        candidate_name=parsed_candidate.name or "Candidate",
        context=context,
    )
    return {"email_content": email_content}
