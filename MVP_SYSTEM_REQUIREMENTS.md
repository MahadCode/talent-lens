# Talent Lens — MVP System Requirements

**Product:** Recruitment & Talent Intelligence Platform  
**Document type:** MVP Product Requirements (PRD)  
**Source brief:** RC3 – Web Tasks  
**Owner role:** Product Manager  
**Status:** Ready for engineering kickoff  

---

## 1. Product intent

Build an AI-assisted hiring workflow where recruiters publish jobs, candidates apply with resumes, and the system produces **explainable, evidence-linked job-relevance scores**. Humans remain in control of shortlisting, interview decisions, and final outcomes.

**MVP success definition (from brief demo):**  
A recruiter posts a Backend Developer role → 3 candidates apply → system parses resumes, scores with explanations and skill gaps → recruiter shortlists one → generates interview questions → schedules interview → dashboard reflects the change. Reliability and transparent AI beat feature count.

---

## 2. MVP goal & non-goals

### Goal
Ship one reliable end-to-end path covering: auth → jobs → resume parse → semantic match + explainability → application pipeline → interview questions → basic scheduling → recruiter analytics snapshot.

### Non-goals (post-MVP / Phase 2)
- Natural-language talent search across the whole pool  
- Vector resume search UI for free-text recruiter queries  
- Duplicate detection / merge workflow  
- Resume-to-job recommendations for candidates  
- Talent-pool rediscovery on new job publish  
- Side-by-side multi-candidate comparison view  
- Formal fairness test harness / bias audit suite  
- Email/SMS notifications (may be simulated as in-app banners only)  
- DOCX resume upload (PDF only for MVP)  
- Multi-tenant org hierarchy, SSO, or advanced RBAC beyond 2 roles  

---

## 3. Personas & roles

| Role | Primary jobs-to-be-done |
|---|---|
| **Recruiter** | Create/manage jobs, review AI assessments, shortlist/reject, generate questions, schedule interviews, view pipeline analytics |
| **Candidate** | Register, maintain profile, upload resume, apply to jobs, track application status |

**Hard rule:** Candidates must not see recruiter-only data (notes, other applicants’ scores, analytics, interviewer feedback).

---

## 4. MoSCoW scope

### Must have (MVP)

| ID | Capability | Why it is MVP |
|---|---|---|
| M1 | Auth + role-based access | Required for both roles and demo safety |
| M2 | Job create/edit/close/reopen | Demo starts with posting a vacancy |
| M3 | PDF resume upload + structured parse | Core AI evidence input |
| M4 | Candidate apply + status visibility | Pipeline entry |
| M5 | Semantic match score + explanation | Rubric-critical (AI quality) |
| M6 | Skill gap / missing-evidence display | Explicit demo success criterion |
| M7 | Recruiter review: shortlist / reject / notes | Human control |
| M8 | Application status audit trail | Trust + compliance of decisions |
| M9 | Interview question generation + edit | Demo step |
| M10 | Interview schedule (date/time/type/interviewer) | Demo step |
| M11 | Recruiter dashboard KPIs | Demo “dashboard updates” |
| M12 | Graceful parse/match failures | Engineering quality |

### Should have (if time after Must)

| ID | Capability |
|---|---|
| S1 | AI extraction of requirements from free-text JD |
| S2 | Skill synonym normalization (e.g. JS ↔ JavaScript) |
| S3 | Candidate correction of parsed skills |
| S4 | Recruiter correction of extracted skills |
| S5 | Manual filters + score override on applicant list |
| S6 | Learning-area suggestions for gaps |
| S7 | Interviewer structured feedback form |
| S8 | Final decision recording (Selected / Rejected) |
| S9 | Charts: apps by stage, shortlist rate, avg processing time |
| S10 | Common skill-gap aggregate across applicants for a job |
| S11 | Hallucination guard: link claims to resume excerpts; flag unsupported |

### Could have (stretch / Phase 2)

All items in §3.10 Advanced Talent Intelligence from the brief, plus DOCX support and real notifications.

### Won’t have (this MVP)

Hardcoded “fake AI” responses, unprotected attribute scoring, candidate access to other applicants, auto-hire without human action.

---

## 5. Functional requirements

### 5.1 Authentication & access control — M1

| Req ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-AUTH-01 | Users can register as Recruiter or Candidate | Role stored; cannot elevate via client |
| FR-AUTH-02 | Login / logout with secure password hashing | Passwords never stored plaintext; invalid creds rejected |
| FR-AUTH-03 | Session/token management | Protected routes require valid auth |
| FR-AUTH-04 | Role-based dashboards | Recruiter routes blocked for candidates and vice versa |
| FR-AUTH-05 | Input validation on auth forms | Empty/invalid email/password handled with clear errors |

### 5.2 Job posting & management — M2 (+ S1)

| Req ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-JOB-01 | Create job with title, department, location, type, salary, description | Persisted and visible to authorized recruiters |
| FR-JOB-02 | Specify required/preferred skills, experience, qualifications, skill importance weights | Stored structured; used by matcher |
| FR-JOB-03 | Edit / close / reopen job | Status changes reflected in listings and apply eligibility |
| FR-JOB-04 | List vacancies with applicant counts | Count updates when applications submitted |
| FR-JOB-05 *(Should)* | Extract requirements from free-text description via AI | Extracted skills editable before save |

### 5.3 Resume upload & parsing — M3 (+ S2, S3)

| Req ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-RES-01 | Candidate uploads PDF resume (max size enforced) | Non-PDF rejected with clear message |
| FR-RES-02 | Extract name, contact, skills, education, experience, projects | Structured record saved |
| FR-RES-03 | Parsing failure / empty / unsupported handled | Status = parse failed; no silent crash |
| FR-RES-04 | Store structured results linked to candidate | Reusable across applications |
| FR-RES-05 *(Should)* | Normalize equivalent skill terms | JS and JavaScript treated as same skill family |
| FR-RES-06 *(Should)* | Candidate can correct extracted fields | Corrections versioned or overwrite with timestamp |

### 5.4 Candidate matching — M5 (+ S5)

| Req ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-MATCH-01 | Score candidate vs job using semantic similarity (not keyword-only) | Real LLM/embeddings; no hardcoded scores |
| FR-MATCH-02 | Default weight model: Skills 50%, Experience 25%, Projects 15%, Qualifications 10% | Weights configurable in code/config; documented if changed |
| FR-MATCH-03 | Produce overall job-relevance score 0–100 (or equivalent) | Visible on recruiter applicant view |
| FR-MATCH-04 | Rank applicants for a job by score | Deterministic sort with ties broken stably |
| FR-MATCH-05 *(Should)* | Recruiter filters + manual score/status override | Override logged in audit trail |

### 5.5 Skill gap & explainability — M6 (+ S4, S6, S11)

| Req ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-EXP-01 | Show matched skills with supporting resume evidence | Each match cites excerpt or structured field |
| FR-EXP-02 | Distinguish **missing evidence** vs **confirmed absence** | UI labels differ (e.g. “Not found in resume” vs “Contradicted”) |
| FR-EXP-03 | Explain recommendation in human-readable form | Recruiter can justify shortlist from explanation alone |
| FR-EXP-04 *(Should)* | Suggest learning areas for gaps | Tips tied to missing required skills |
| FR-EXP-05 *(Should)* | Recruiter can correct extracted skills | Re-score optional or flagged stale |
| FR-EXP-06 *(Should)* | Flag unsupported AI claims | Claims without excerpt marked for review |

### 5.6 Application pipeline — M4, M7, M8

| Req ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-APP-01 | Candidate applies to an open job (with resume on file) | Duplicate apply to same job blocked or upserted clearly |
| FR-APP-02 | Candidate sees own application status only | No cross-candidate leakage |
| FR-APP-03 | Recruiter can shortlist, reject, or advance manually | Status update immediate |
| FR-APP-04 | Private recruiter notes on application | Notes invisible to candidates |
| FR-APP-05 | Audit trail of status changes | Actor, from→to, timestamp stored |
| FR-APP-06 | MVP status model | `Submitted → Parsed → AI Assessment Available → Recruiter Review → Shortlisted \| Rejected → Interview → Selected \| Rejected` |

### 5.7 Interview question generation — M9

| Req ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-IQ-01 | Generate role-specific questions | Tied to job skills + candidate profile |
| FR-IQ-02 | Support beginner / intermediate / advanced difficulty | At least one question per difficulty or selectable |
| FR-IQ-03 | Include project-based questions + answer guidelines | Guidelines visible to recruiter only |
| FR-IQ-04 | Recruiter can edit, remove, regenerate questions | Edits persisted |

### 5.8 Interview scheduling & feedback — M10 (+ S7, S8)

| Req ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-INT-01 | Schedule interview: date, time, interviewer, type | Linked to application; appears on schedules list |
| FR-INT-02 | Show interview schedules to recruiter | List/calendar-lite view acceptable |
| FR-INT-03 | Flag obvious conflicts for same interviewer/time | Warning shown; soft-block acceptable for MVP |
| FR-INT-04 *(Should)* | Store structured interviewer feedback | Ratings + comments fields |
| FR-INT-05 *(Should)* | Record final decision by authorized recruiter | Moves application to Selected/Rejected |
| FR-INT-06 | Notifications may be simulated | In-app status change is enough |

### 5.9 Recruitment analytics — M11 (+ S9, S10)

| Req ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-AN-01 | Dashboard shows: active jobs, applications, shortlisted, pending reviews, upcoming interviews | Numbers match live data after demo actions |
| FR-AN-02 *(Should)* | Charts by job and pipeline stage | At least one chart type |
| FR-AN-03 *(Should)* | Application-to-shortlist rate + avg processing time | Formula documented |
| FR-AN-04 *(Should)* | Common skill gaps across applicants for a job | Aggregated missing required skills |

---

## 6. Non-functional requirements

| ID | Area | Requirement |
|---|---|---|
| NFR-01 | Security | Password hashing, auth on all mutating APIs, role checks server-side |
| NFR-02 | Validation | Server-side validation for uploads, job fields, status transitions |
| NFR-03 | Reliability | Parse/match failures do not take down the app; retries or clear error states |
| NFR-04 | AI integrity | No hardcoded AI feature stubs; real model/embeddings calls |
| NFR-05 | Explainability | Every score shown to recruiters includes evidence or explicit “no evidence” |
| NFR-06 | Performance (MVP) | Single-job applicant list (≤50) loads in interactive time; match may be async |
| NFR-07 | Observability | Log AI failures and parse errors for debugging |
| NFR-08 | Code quality | Clear module boundaries (API, domain, AI agents, UI) |
| NFR-09 | Deployment | Runnable locally with documented setup (README sufficient for MVP) |

---

## 7. Suggested domain model (MVP)

- **User** (role: recruiter \| candidate)  
- **Job** (fields + status open/closed + skill requirements + weights)  
- **CandidateProfile** (contact, parsed resume JSON, corrections)  
- **Resume** (file meta, parse status, raw/structured text)  
- **Application** (job, candidate, status, score snapshot, notes)  
- **MatchResult** (subscores, matched skills, gaps, evidence links, explanation)  
- **StatusEvent** (audit)  
- **InterviewQuestionSet** (questions, difficulty, guidelines, edits)  
- **Interview** (schedule fields, conflict flag, feedback, decision)  

---

## 8. End-to-end acceptance scenario (must pass)

1. Recruiter registers/logs in and creates **Backend Developer** job requiring **Python, Django, PostgreSQL, Docker**.  
2. Three candidates register, upload PDFs, and apply.  
3. System parses each resume into structured skills/experience/projects.  
4. System produces a job-relevance score + explanation + missing evidence for each.  
5. Recruiter opens ranked list, reviews explanations, **shortlists one**.  
6. Recruiter **generates interview questions**, edits at least one.  
7. Recruiter **schedules an interview**.  
8. Dashboard counts (applications, shortlisted, interviews) update correctly.  

**Pass bar:** workflow completes without manual DB edits; AI outputs are evidence-linked; humans control shortlist/decision.

---

## 9. Evaluation alignment (how MVP scores)

| Rubric area | Marks | MVP coverage |
|---|---|---|
| Architecture & functional completeness | 30 | M1–M12 full pipeline |
| AI implementation & matching quality | 25 | Semantic match + weights + explanations |
| Resume parsing & extraction | 15 | PDF parse + structured store + failure handling |
| UI & experience | 15 | Role dashboards, clear evidence UI, status visibility |
| Innovation, testing, security & deployment | 15 | Auth security, audit trail, evidence flags, local deploy docs; add basic tests for auth/status/match contract |

---

## 10. Delivery slices (recommended build order)

| Sprint slice | Deliverable | Demoable outcome |
|---|---|---|
| **Slice 1** | Auth + roles + empty dashboards | Two users land on correct home |
| **Slice 2** | Jobs CRUD + candidate apply shell | Job exists; application created |
| **Slice 3** | Resume upload + parse pipeline | Structured resume on profile |
| **Slice 4** | Matching + explainability + ranking | Scores + gaps on recruiter view |
| **Slice 5** | Pipeline actions + audit + notes | Shortlist/reject with history |
| **Slice 6** | Interview questions + scheduling | Demo scenario completable |
| **Slice 7** | Dashboard analytics + polish + tests | Rubric-ready demo |

---

## 11. Open product decisions (resolve before build)

1. **Match sync vs async:** Prefer async job with “AI Assessment Available” status for MVP reliability.  
2. **Score override:** Allow recruiter override in Should scope only if Slice 5 finishes early.  
3. **Candidate job browse:** MVP needs list of open jobs + apply; advanced recommendations deferred.  
4. **Interviewer identity:** Free-text interviewer name is enough for MVP (no separate interviewer role).  
5. **Data retention:** Keep all applications for demo; no auto-purge in MVP.

---

## 12. Out-of-scope reminder (Phase 2 backlog)

From brief §3.10 — track as future epics, not MVP blockers:

1. NL talent search  
2. Semantic resume corpus search  
3. Duplicate application detection  
4. Job recommendations to candidates  
5. Talent pool discovery on new jobs  
6. Candidate comparison matrix  
7. Formal fairness/bias safeguards suite  
8. Full hallucination verification workflow beyond excerpt linking  

---

*This MVP is intentionally narrower than the full brief so the team can hit the demo success criterion with real AI, clean architecture, and human-controlled hiring decisions.*
