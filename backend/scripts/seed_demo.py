"""Wipe and seed a full Talent Lens demo: 3 companies, staff, jobs, 20 PDF applicants."""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete  # noqa: E402

from app.core.constants import (  # noqa: E402
    CandidateStatus,
    HiringDecision,
    InterviewType,
    JobStatus,
    UserRole,
)
from app.core.security import hash_password  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import AsyncSessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    Candidate,
    CandidateNote,
    CandidateStatusEvent,
    EmailLog,
    Interview,
    Job,
    Resume,
    ScheduledInterview,
    Score,
    User,
)
from ai_agents.utils.schemas import EmailType  # noqa: E402
from scripts.pdf import write_text_pdf  # noqa: E402

DEMO_PASSWORD = "DemoPass123"
RESUME_DIR = Path(__file__).resolve().parents[1] / "uploads" / "seed_resumes"
NOW = datetime.now(timezone.utc)


def _profile(**kwargs) -> dict:
    base = {
        "name": kwargs.get("name"),
        "email": kwargs.get("email"),
        "phone": kwargs.get("phone", "+1-415-555-0100"),
        "skills": kwargs.get("skills", []),
        "experience": kwargs.get("experience", []),
        "education": kwargs.get("education", []),
        "projects": kwargs.get("projects", []),
        "certifications": kwargs.get("certifications", []),
        "github": kwargs.get("github"),
        "linkedin": kwargs.get("linkedin"),
    }
    return base


def _match(pct: float, missing: list[str], extra: list[str], comparison: str, explanation: str) -> dict:
    return {
        "match_percentage": pct,
        "missing_skills": missing,
        "extra_skills": extra,
        "experience_comparison": comparison,
        "explanation": explanation,
    }


CANDIDATES: list[dict] = [
    {
        "name": "Priya Nair",
        "email": "priya.nair@example.com",
        "job": "smart-contract",
        "status": CandidateStatus.SHORTLISTED,
        "skills": ["Solidity", "Foundry", "Ethereum", "TypeScript", "The Graph"],
        "experience": ["4 years building DeFi vaults at a trading desk", "Led an audit remediation for an ERC-20 staking pool"],
        "education": ["B.S. Computer Science, University of Waterloo"],
        "projects": ["Open-source gas-optimized vesting contract"],
        "certifications": ["Certified Ethereum Developer"],
        "github": "https://github.com/priyanair",
        "score": (88, 84, 80, 78, 70, 84),
        "missing": ["Formal verification"],
        "extra": ["The Graph"],
        "note": "Strong Solidity depth. Move to interview this week.",
    },
    {
        "name": "Jonah Vest",
        "email": "jonah.vest@example.com",
        "job": "smart-contract",
        "status": CandidateStatus.INTERVIEWING,
        "skills": ["Solidity", "Rust", "Anchor", "Ethereum", "Security reviews"],
        "experience": ["3 years protocol engineering", "Shipped two mainnet token launches"],
        "education": ["M.S. Distributed Systems, TU Delft"],
        "projects": ["Reentrancy test harness used in internal audits"],
        "certifications": [],
        "github": "https://github.com/jonahvest",
        "score": (86, 82, 85, 80, 40, 81),
        "missing": ["Foundry"],
        "extra": ["Anchor", "Rust"],
        "note": "Booked for a video interview with the protocol lead.",
        "interview": True,
        "schedule": True,
    },
    {
        "name": "Elena Voss",
        "email": "elena.voss@example.com",
        "job": "smart-contract",
        "status": CandidateStatus.PARSED,
        "skills": ["Solidity", "Hardhat", "JavaScript", "ERC-20"],
        "experience": ["2 years fullstack, 1 year contracts"],
        "education": ["B.Eng. Software, ETH Zurich"],
        "projects": ["NFT minting contract for a campus club"],
        "certifications": [],
        "github": "https://github.com/elenavoss",
        "score": (72, 61, 68, 82, 20, 66),
        "missing": ["Foundry", "Mainnet production experience"],
        "extra": ["Hardhat"],
    },
    {
        "name": "Samir Haddad",
        "email": "samir.haddad@example.com",
        "job": "smart-contract",
        "status": CandidateStatus.REJECTED,
        "skills": ["Python", "Django", "SQL"],
        "experience": ["5 years backend web apps, no chain work"],
        "education": ["B.S. Information Systems, AUB"],
        "projects": ["Internal billing API"],
        "certifications": ["AWS Cloud Practitioner"],
        "github": None,
        "score": (38, 44, 30, 70, 40, 42),
        "missing": ["Solidity", "Ethereum", "Foundry"],
        "extra": ["Django"],
        "note": "Strong engineer, wrong stack for this role.",
    },
    {
        "name": "Willa Chen",
        "email": "willa.chen@example.com",
        "job": "market-analyst",
        "status": CandidateStatus.SHORTLISTED,
        "skills": ["Python", "Pandas", "On-chain analytics", "Dune", "SQL"],
        "experience": ["3 years crypto research desk", "Weekly BTC/ETH market notes"],
        "education": ["B.A. Economics, UCLA"],
        "projects": ["Open dashboard of DEX volumes"],
        "certifications": ["CFA Level I"],
        "github": "https://github.com/willachen",
        "score": (90, 86, 75, 80, 72, 85),
        "missing": ["Rust"],
        "extra": ["Dune"],
        "note": "Best research writing in this batch.",
    },
    {
        "name": "Tomas Reeve",
        "email": "tomas.reeve@example.com",
        "job": "market-analyst",
        "status": CandidateStatus.MANUAL_REVIEW,
        "skills": ["Excel", "SQL", "Tableau", "Python"],
        "experience": ["6 years traditional equity research, 6 months crypto"],
        "education": ["MBA, Booth"],
        "projects": ["Earnings model library"],
        "certifications": ["CFA Charterholder"],
        "github": None,
        "score": (64, 78, 50, 88, 90, 72),
        "missing": ["Dune", "On-chain analytics"],
        "extra": ["Tableau", "CFA"],
        "note": "Domain shift — human review before shortlist.",
        "override": True,
    },
    {
        "name": "Asha Okonkwo",
        "email": "asha.okonkwo@example.com",
        "job": "market-analyst",
        "status": CandidateStatus.PARSED,
        "skills": ["Python", "NumPy", "News sentiment", "NLP"],
        "experience": ["2 years ML internships, one crypto hackathon"],
        "education": ["B.S. Statistics, University of Lagos"],
        "projects": ["Headline sentiment bot for BTC"],
        "certifications": [],
        "github": "https://github.com/ashaokonkwo",
        "score": (70, 55, 78, 76, 10, 64),
        "missing": ["Dune", "Desk experience"],
        "extra": ["NLP"],
    },
    {
        "name": "Leo Hart",
        "email": "leo.hart@example.com",
        "job": "platform",
        "status": CandidateStatus.HIRED,
        "skills": ["Go", "Kubernetes", "PostgreSQL", "gRPC", "Terraform"],
        "experience": ["7 years platform engineering", "Ran a 40-node k8s fleet"],
        "education": ["B.S. Computer Engineering, Georgia Tech"],
        "projects": ["Internal developer portal"],
        "certifications": ["CKA"],
        "github": "https://github.com/leohart",
        "score": (93, 94, 82, 80, 85, 91),
        "missing": [],
        "extra": ["gRPC"],
        "note": "Offer accepted. Start date next month.",
        "interview": True,
        "schedule": True,
        "decision": HiringDecision.HIRED,
    },
    {
        "name": "Nia Brooks",
        "email": "nia.brooks@example.com",
        "job": "platform",
        "status": CandidateStatus.INTERVIEWING,
        "skills": ["Go", "Python", "Kubernetes", "AWS", "PostgreSQL"],
        "experience": ["5 years SRE, 2 years platform"],
        "education": ["B.S. Computer Science, Howard University"],
        "projects": ["Autoscaling worker pool"],
        "certifications": ["AWS Solutions Architect"],
        "github": "https://github.com/niabrooks",
        "score": (84, 88, 70, 78, 80, 83),
        "missing": ["Terraform"],
        "extra": ["AWS"],
        "interview": True,
        "schedule": True,
    },
    {
        "name": "Pavel Dvorak",
        "email": "pavel.dvorak@example.com",
        "job": "platform",
        "status": CandidateStatus.SHORTLISTED,
        "skills": ["Rust", "Go", "Linux", "PostgreSQL", "Observability"],
        "experience": ["4 years infrastructure at a payments firm"],
        "education": ["M.S. Computer Science, Charles University"],
        "projects": ["eBPF tracing demo"],
        "certifications": [],
        "github": "https://github.com/paveldvorak",
        "score": (80, 82, 74, 84, 20, 78),
        "missing": ["Kubernetes"],
        "extra": ["Rust", "eBPF"],
    },
    {
        "name": "Yara Mensah",
        "email": "yara.mensah@example.com",
        "job": "auditor",
        "status": CandidateStatus.MANUAL_REVIEW,
        "skills": ["Solidity", "Slither", "Mythril", "Python", "Threat modeling"],
        "experience": ["2 years security analyst, 1 year contract audits"],
        "education": ["B.S. Cybersecurity, Ashesi University"],
        "projects": ["Reentrancy checklist published on GitHub"],
        "certifications": ["OSCP"],
        "github": "https://github.com/yaramensah",
        "score": (78, 70, 72, 74, 88, 75),
        "missing": ["Formal verification", "Mainnet audit lead"],
        "extra": ["OSCP"],
        "note": "Junior for a lead auditor seat — review anyway.",
    },
    {
        "name": "Kit Solano",
        "email": "kit.solano@example.com",
        "job": "auditor",
        "status": CandidateStatus.PARSED,
        "skills": ["Solidity", "Echidna", "Foundry", "Rust"],
        "experience": ["3 years audit associate"],
        "education": ["B.S. Mathematics, UNAM"],
        "projects": ["Fuzzing suite for AMM invariants"],
        "certifications": [],
        "github": "https://github.com/kitsolano",
        "score": (82, 76, 88, 72, 15, 76),
        "missing": ["Client-facing report writing"],
        "extra": ["Echidna"],
    },
    {
        "name": "Rowan Blake",
        "email": "rowan.blake@example.com",
        "job": "auditor",
        "status": CandidateStatus.REJECTED,
        "skills": ["Java", "Spring", "OWASP"],
        "experience": ["8 years enterprise AppSec, no smart contracts"],
        "education": ["B.S. Computer Science, University of Manchester"],
        "projects": ["SAST rollout at a bank"],
        "certifications": ["CISSP"],
        "github": None,
        "score": (40, 60, 35, 75, 80, 52),
        "missing": ["Solidity", "EVM"],
        "extra": ["CISSP", "Java"],
    },
    {
        "name": "Ines Duarte",
        "email": "ines.duarte@example.com",
        "job": "fullstack",
        "status": CandidateStatus.SHORTLISTED,
        "skills": ["TypeScript", "React", "Next.js", "Node.js", "PostgreSQL"],
        "experience": ["5 years product engineering", "Shipped two SaaS dashboards"],
        "education": ["B.S. Informatics, University of Porto"],
        "projects": ["Open-source table component"],
        "certifications": [],
        "github": "https://github.com/inesduarte",
        "score": (90, 86, 84, 78, 20, 82),
        "missing": ["GraphQL"],
        "extra": ["Next.js"],
        "note": "Fits the product team immediately.",
    },
    {
        "name": "Micah Lang",
        "email": "micah.lang@example.com",
        "job": "fullstack",
        "status": CandidateStatus.INTERVIEWING,
        "skills": ["TypeScript", "React", "Python", "FastAPI", "PostgreSQL"],
        "experience": ["4 years full-stack at a climate startup"],
        "education": ["B.A. Cognitive Science, UCSD"],
        "projects": ["Realtime collaboration canvas"],
        "certifications": [],
        "github": "https://github.com/micahlang",
        "score": (85, 80, 88, 74, 10, 79),
        "missing": ["Next.js"],
        "extra": ["FastAPI"],
        "interview": True,
        "schedule": True,
    },
    {
        "name": "Sora Kim",
        "email": "sora.kim@example.com",
        "job": "fullstack",
        "status": CandidateStatus.NEW,
        "skills": ["JavaScript", "React", "CSS"],
        "experience": ["1 year junior frontend"],
        "education": ["Bootcamp, Recurse Center"],
        "projects": ["Personal portfolio"],
        "certifications": [],
        "github": "https://github.com/sorakim",
        "parsed": False,
    },
    {
        "name": "Adeel Farooq",
        "email": "adeel.farooq@example.com",
        "job": "fullstack",
        "status": CandidateStatus.PARSED,
        "skills": ["TypeScript", "React", "Node.js", "MongoDB"],
        "experience": ["3 years agency work"],
        "education": ["B.S. Software Engineering, NUST"],
        "projects": ["Headless CMS theme"],
        "certifications": [],
        "github": "https://github.com/adeelfarooq",
        "score": (74, 70, 68, 76, 15, 69),
        "missing": ["PostgreSQL", "Next.js"],
        "extra": ["MongoDB"],
    },
    {
        "name": "Hana Idris",
        "email": "hana.idris@example.com",
        "job": "ml",
        "status": CandidateStatus.HIRED,
        "skills": ["Python", "PyTorch", "LangChain", "RAG", "PostgreSQL"],
        "experience": ["6 years ML engineer", "Shipped a retrieval pipeline to prod"],
        "education": ["Ph.D. Machine Learning, KAUST"],
        "projects": ["Citation-grounded answer engine"],
        "certifications": [],
        "github": "https://github.com/hanaidris",
        "score": (94, 92, 90, 95, 30, 90),
        "missing": [],
        "extra": ["LangChain"],
        "note": "Hired for the closed ML role. Keep the file for reference.",
        "interview": True,
        "schedule": True,
        "decision": HiringDecision.HIRED,
    },
    {
        "name": "Quinn Adler",
        "email": "quinn.adler@example.com",
        "job": "ml",
        "status": CandidateStatus.NOT_HIRED,
        "skills": ["Python", "scikit-learn", "SQL"],
        "experience": ["2 years data analyst"],
        "education": ["B.S. Applied Math, University of Toronto"],
        "projects": ["Churn model notebook"],
        "certifications": [],
        "github": None,
        "score": (58, 50, 45, 80, 10, 52),
        "missing": ["PyTorch", "Production ML"],
        "extra": ["scikit-learn"],
        "interview": True,
        "schedule": True,
        "decision": HiringDecision.NOT_HIRED,
    },
    {
        "name": "Bea Solis",
        "email": "bea.solis@example.com",
        "job": "ml",
        "status": CandidateStatus.NEW,
        "skills": ["Python", "Pandas"],
        "experience": ["Fresh graduate"],
        "education": ["B.S. Data Science, University of the Philippines"],
        "projects": ["Kaggle housing prices"],
        "certifications": [],
        "github": "https://github.com/beasolis",
        "parsed": False,
    },
]


JOBS = {
    "smart-contract": {
        "title": "Smart Contract Engineer",
        "company": "Halden Capital",
        "status": JobStatus.OPEN,
        "description": (
            "Halden Capital is hiring a smart contract engineer to design, test, and ship "
            "token and vault contracts on Ethereum. You will work with research on fee logic "
            "and with security on audit readiness."
        ),
        "requirements": "Solidity, Foundry, Ethereum, ERC-20, testing, 3+ years, security awareness.",
        "extracted": {
            "required_skills": ["Solidity", "Foundry", "Ethereum"],
            "preferred_skills": ["Formal verification", "The Graph"],
            "experience": "3+ years shipping contracts",
            "qualifications": ["Production mainnet experience"],
        },
    },
    "market-analyst": {
        "title": "Crypto Market Analyst",
        "company": "Halden Capital",
        "status": JobStatus.OPEN,
        "description": (
            "Write daily market notes, monitor on-chain flows, and brief the investment committee "
            "on BTC, ETH, and sector sentiment."
        ),
        "requirements": "Python, SQL, on-chain analytics, Dune, research writing, 2+ years.",
        "extracted": {
            "required_skills": ["Python", "SQL", "On-chain analytics", "Dune"],
            "preferred_skills": ["CFA"],
            "experience": "2+ years research desk",
            "qualifications": ["Clear written communication"],
        },
    },
    "platform": {
        "title": "Platform Engineer",
        "company": "Tessel Network",
        "status": JobStatus.OPEN,
        "description": (
            "Tessel Network runs validator and indexer infrastructure. Build internal platforms "
            "so protocol teams can ship without opening tickets for every cluster."
        ),
        "requirements": "Go, Kubernetes, PostgreSQL, Terraform, 4+ years platform or SRE.",
        "extracted": {
            "required_skills": ["Go", "Kubernetes", "PostgreSQL", "Terraform"],
            "preferred_skills": ["gRPC", "Observability"],
            "experience": "4+ years platform/SRE",
            "qualifications": ["Production Kubernetes"],
        },
    },
    "auditor": {
        "title": "Protocol Auditor",
        "company": "Tessel Network",
        "status": JobStatus.OPEN,
        "description": (
            "Review Tessel contracts and partner integrations. Produce evidence-linked findings, "
            "not generic checklists."
        ),
        "requirements": "Solidity, EVM, Slither or equivalent, threat modeling, 2+ years audits.",
        "extracted": {
            "required_skills": ["Solidity", "EVM", "Threat modeling"],
            "preferred_skills": ["Echidna", "Formal verification"],
            "experience": "2+ years audits",
            "qualifications": ["Written security reports"],
        },
    },
    "fullstack": {
        "title": "Full-Stack Engineer",
        "company": "Northline Labs",
        "status": JobStatus.OPEN,
        "description": (
            "Northline Labs builds operator tools for research teams. You will own features from "
            "Postgres to React, including the hiring console you are looking at."
        ),
        "requirements": "TypeScript, React, Next.js, Node.js, PostgreSQL, 3+ years product engineering.",
        "extracted": {
            "required_skills": ["TypeScript", "React", "Next.js", "PostgreSQL"],
            "preferred_skills": ["GraphQL", "FastAPI"],
            "experience": "3+ years product engineering",
            "qualifications": ["Shipped production UI"],
        },
    },
    "ml": {
        "title": "Machine Learning Engineer",
        "company": "Northline Labs",
        "status": JobStatus.CLOSED,
        "description": (
            "Build retrieval and scoring pipelines for document-heavy products. This role is closed "
            "but retained so you can inspect hired and not-hired outcomes."
        ),
        "requirements": "Python, PyTorch, RAG, production ML, 4+ years.",
        "extracted": {
            "required_skills": ["Python", "PyTorch", "RAG"],
            "preferred_skills": ["LangChain"],
            "experience": "4+ years ML engineering",
            "qualifications": ["Production retrieval systems"],
        },
    },
}


COMPANIES = [
    {
        "name": "Halden Capital",
        "jobs": ["smart-contract", "market-analyst"],
        "staff": [
            ("Ilan Brooks", "admin@haldencapital.example", UserRole.ADMIN),
            ("Sofia Rahman", "hr@haldencapital.example", UserRole.HR_MANAGER),
            ("Jonah Pell", "recruiter@haldencapital.example", UserRole.RECRUITER),
            ("Amira Cole", "interviewer@haldencapital.example", UserRole.INTERVIEWER),
        ],
    },
    {
        "name": "Tessel Network",
        "jobs": ["platform", "auditor"],
        "staff": [
            ("Rhea Okafor", "admin@tessel.example", UserRole.ADMIN),
            ("Marcus Lin", "hr@tessel.example", UserRole.HR_MANAGER),
            ("Dana Ruiz", "recruiter@tessel.example", UserRole.RECRUITER),
            ("Owen Park", "interviewer@tessel.example", UserRole.INTERVIEWER),
        ],
    },
    {
        "name": "Northline Labs",
        "jobs": ["fullstack", "ml"],
        "staff": [
            ("Mara Elling", "admin@northline.example", UserRole.ADMIN),
            ("Chris Adeyemi", "hr@northline.example", UserRole.HR_MANAGER),
            ("Lina Cho", "recruiter@northline.example", UserRole.RECRUITER),
            ("Theo Berg", "interviewer@northline.example", UserRole.INTERVIEWER),
        ],
    },
]


def _resume_lines(person: dict, job_title: str) -> list[str]:
    lines = [
        person["email"],
        person.get("github") or "",
        "",
        f"Applying for: {job_title}",
        "",
        "Skills",
        ", ".join(person.get("skills") or []),
        "",
        "Experience",
        *person.get("experience", []),
        "",
        "Education",
        *person.get("education", []),
        "",
        "Projects",
        *person.get("projects", []),
        "",
        "Certifications",
        ", ".join(person.get("certifications") or []) or "None",
    ]
    return [line for line in lines if line is not None]


def _question_set(focus: str) -> list[dict]:
    return [
        {
            "id": str(uuid.uuid4()),
            "question": f"Walk through a recent {focus} problem you owned end to end.",
            "focus_area": "experience",
            "difficulty": "beginner",
            "guideline": "Look for ownership, constraints, and a concrete outcome.",
            "is_follow_up": False,
        },
        {
            "id": str(uuid.uuid4()),
            "question": f"How would you debug a production incident in {focus}?",
            "focus_area": "systems",
            "difficulty": "intermediate",
            "guideline": "Expect a systematic debug path, not a tool dump.",
            "is_follow_up": False,
        },
        {
            "id": str(uuid.uuid4()),
            "question": f"Design a safer architecture for a high-risk {focus} component.",
            "focus_area": "architecture",
            "difficulty": "advanced",
            "guideline": "Score trade-offs, failure modes, and testing.",
            "is_follow_up": False,
        },
        {
            "id": str(uuid.uuid4()),
            "question": "Tell us about a project on your resume that would transfer to this role.",
            "focus_area": "project",
            "difficulty": "intermediate",
            "guideline": "Map their project to this job's required skills.",
            "is_follow_up": False,
        },
    ]


async def _wipe(session) -> None:
    for table in reversed(Base.metadata.sorted_tables):
        await session.execute(delete(table))


async def seed() -> None:
    password_hash = hash_password(DEMO_PASSWORD)
    RESUME_DIR.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await _wipe(session)

        staff_by_company: dict[str, dict[str, User]] = {}
        for company in COMPANIES:
            roles: dict[str, User] = {}
            for full_name, email, role in company["staff"]:
                user = User(
                    full_name=full_name,
                    email=email,
                    hashed_password=password_hash,
                    role=role,
                    company_name=company["name"],
                    is_active=True,
                    is_verified=True,
                    two_factor_enabled=False,
                )
                session.add(user)
                roles[role.value] = user
            staff_by_company[company["name"]] = roles

        await session.flush()

        job_rows: dict[str, Job] = {}
        for key, spec in JOBS.items():
            creator = staff_by_company[spec["company"]]["RECRUITER"]
            job = Job(
                title=spec["title"],
                description=spec["description"],
                requirements=spec["requirements"],
                extracted_requirements=spec["extracted"],
                status=spec["status"],
                created_by_id=creator.id,
            )
            session.add(job)
            job_rows[key] = job

        await session.flush()

        print("\n=== Talent Lens demo seed ===")
        print(f"Password for every account: {DEMO_PASSWORD}\n")
        print("Staff logins")
        for company in COMPANIES:
            print(f"  {company['name']}")
            for full_name, email, role in company["staff"]:
                print(f"    {role.value:<12} {email:<32} {full_name}")

        print("\nCandidate logins (portal at /app)")
        for index, person in enumerate(CANDIDATES):
            job = job_rows[person["job"]]
            company_name = JOBS[person["job"]]["company"]
            recruiter = staff_by_company[company_name]["RECRUITER"]
            interviewer = staff_by_company[company_name]["INTERVIEWER"]
            parsed = person.get("parsed", True)

            account = User(
                full_name=person["name"],
                email=person["email"],
                hashed_password=password_hash,
                role=UserRole.CANDIDATE,
                company_name=None,
                is_active=True,
                is_verified=True,
                two_factor_enabled=False,
            )
            session.add(account)
            await session.flush()

            filename = f"{person['name'].lower().replace(' ', '_')}.pdf"
            pdf_path = RESUME_DIR / filename
            write_text_pdf(pdf_path, person["name"], _resume_lines(person, job.title))
            extracted = "\n".join(_resume_lines(person, job.title))

            profile = None
            matching = None
            match_pct = None
            if parsed:
                profile = _profile(
                    name=person["name"],
                    email=person["email"],
                    skills=person.get("skills"),
                    experience=person.get("experience"),
                    education=person.get("education"),
                    projects=person.get("projects"),
                    certifications=person.get("certifications"),
                    github=person.get("github"),
                )
                score_tuple = person.get("score")
                match_pct = float(score_tuple[5]) if score_tuple else 50.0
                matching = _match(
                    match_pct,
                    person.get("missing", []),
                    person.get("extra", []),
                    f"{person['name']}'s background versus {job.title}.",
                    f"Seeded assessment for {person['name']} on {job.title}.",
                )

            candidate = Candidate(
                job_id=job.id,
                user_id=account.id,
                full_name=person["name"],
                email=person["email"],
                github_url=person.get("github"),
                status=person["status"],
                parsed_profile=profile,
                match_percentage=match_pct,
                matching_result=matching,
                score_overridden=bool(person.get("override")),
                created_at=NOW - timedelta(days=20 - index),
            )
            session.add(candidate)
            await session.flush()

            session.add(
                Resume(
                    candidate_id=candidate.id,
                    file_path=str(pdf_path),
                    original_filename=filename,
                    extracted_text=extracted,
                )
            )

            if parsed and person.get("score"):
                skills, experience, projects, education, certs, total = person["score"]
                session.add(
                    Score(
                        candidate_id=candidate.id,
                        skills_score=skills,
                        experience_score=experience,
                        projects_score=projects,
                        education_score=education,
                        certifications_score=certs,
                        total_score=total,
                        reasoning=f"Seeded score for {person['name']}: total {total}/100.",
                    )
                )

            if person["status"] != CandidateStatus.NEW:
                session.add(
                    CandidateStatusEvent(
                        candidate_id=candidate.id,
                        actor_id=recruiter.id,
                        from_status=CandidateStatus.NEW,
                        to_status=CandidateStatus.PARSED,
                    )
                )
            if person["status"] not in {CandidateStatus.NEW, CandidateStatus.PARSED}:
                session.add(
                    CandidateStatusEvent(
                        candidate_id=candidate.id,
                        actor_id=recruiter.id,
                        from_status=CandidateStatus.PARSED,
                        to_status=person["status"],
                    )
                )

            if person.get("note"):
                session.add(
                    CandidateNote(
                        candidate_id=candidate.id,
                        author_id=recruiter.id,
                        body=person["note"],
                    )
                )

            if person.get("interview"):
                session.add(
                    Interview(
                        candidate_id=candidate.id,
                        questions=_question_set(job.title),
                        overall_assessment=(
                            f"{person['name']} showed clear reasoning on {job.title} topics."
                            if person["status"] in {CandidateStatus.HIRED, CandidateStatus.INTERVIEWING}
                            else f"{person['name']} did not demonstrate enough depth for {job.title}."
                        ),
                        passed=person["status"] in {CandidateStatus.HIRED, CandidateStatus.INTERVIEWING},
                    )
                )

            if person.get("schedule"):
                when = NOW + timedelta(days=2 + (index % 5), hours=10)
                session.add(
                    ScheduledInterview(
                        candidate_id=candidate.id,
                        scheduled_at=when,
                        interviewer_name=interviewer.full_name,
                        interview_type=InterviewType.VIDEO,
                        notes=f"Seeded {InterviewType.VIDEO.value} with {interviewer.full_name}.",
                        feedback={"comments": "Seeded feedback: prepared and concise."}
                        if person.get("decision")
                        else None,
                        decision=person.get("decision"),
                        created_by_id=recruiter.id,
                    )
                )

            if person["status"] == CandidateStatus.SHORTLISTED:
                session.add(
                    EmailLog(
                        candidate_id=candidate.id,
                        email_type=EmailType.SHORTLIST,
                        subject=f"Next step for {job.title}",
                        body=f"Hi {person['name'].split()[0]}, we would like to continue with you for {job.title}.",
                    )
                )
            if person["status"] == CandidateStatus.REJECTED:
                session.add(
                    EmailLog(
                        candidate_id=candidate.id,
                        email_type=EmailType.REJECTION,
                        subject=f"Update on {job.title}",
                        body=f"Hi {person['name'].split()[0]}, we are not moving forward for {job.title}.",
                    )
                )

            print(f"    {person['email']:<32} {person['status'].value:<14} {job.title} ({company_name})")

        await session.commit()

    print("\nOpen http://localhost:3000/login")
    print("Staff land on /dashboard. Candidates land on /app.")
    print(f"Resume PDFs: {RESUME_DIR}")


if __name__ == "__main__":
    asyncio.run(seed())
