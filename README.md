# Talent Lens

Talent Lens is an AI hiring platform for recruiting teams. It parses resumes, matches candidates to job requirements, scores applicants, and supports interviews and scheduling. The API is FastAPI with PostgreSQL (SQLite locally). The web app is Next.js. Gemini runs the LangGraph hiring pipeline. Account email (verification, password reset, optional 2FA) goes out through SendLiberty using a connected Gmail account.

---

## Table of contents

1. [Features](#features)
2. [Tech stack](#tech-stack)
3. [Project structure](#project-structure)
4. [Prerequisites](#prerequisites)
5. [Running locally](#running-locally)
6. [Environment variables](#environment-variables)
7. [Running tests](#running-tests)
8. [API reference](#api-reference)
9. [Deployment](#deployment)
10. [Git workflow](#git-workflow)
11. [Troubleshooting](#troubleshooting)
12. [Contributing](#contributing)
13. [License](#license)

---

## Features

### Authentication and accounts
Register, log in, and refresh JWTs (`Authorization: Bearer`). Roles: `ADMIN`, `HR_MANAGER`, `RECRUITER`, `INTERVIEWER`, `CANDIDATE`.

### Email verification
New accounts cannot use the app until they verify with a 6-digit code or magic link. Existing database users were backfilled as verified in migration `0004`.

### Forgot / reset password
`/forgot-password` emails a reset link and code. `/reset-password` consumes the hashed token.

### Email two-step login
Optional under Settings → Security. When enabled, login sends a one-time code instead of issuing tokens immediately.

### Jobs
HR roles create and edit jobs. Requirements are stored and used by the matcher.

### Candidates and pipeline
Statuses: `NEW` → `PARSED` → `MANUAL_REVIEW` / `SHORTLISTED` / `REJECTED` → `INTERVIEWING` → `HIRED` / `NOT_HIRED`. Notes, status history, and score overrides are supported.

### Resume upload and parse
PDF upload extracts text, then the parser agent builds a structured profile.

### AI match and score
Matcher and scoring agents compare the profile to the job. Results persist on the candidate.

### Interviews and question bank
Generate, edit, and regenerate interview questions. Record an assessment after the interview.

### Scheduling
Book video/other interviews, attach interviewer and notes, record a decision.

### Candidate portal
Candidates use `/app` to browse jobs, apply, view applications, and manage a resume.

### Recruiter dashboard
Funnel counts, latest candidates, analytics, resume screening, notifications, settings.

### Demo seed (local only)
`python -m scripts.seed_demo` wipes the current database and loads demo companies, jobs, and applicants. Password for seeded accounts is `DemoPass123`. Do not run this against a public production database without changing that password.

---

## Tech stack

**Backend:** FastAPI (async), Uvicorn, SQLAlchemy 2, Alembic, PostgreSQL (`asyncpg`) or SQLite (`aiosqlite`), JWT (`python-jose`), passlib/bcrypt, LangChain, LangGraph, Google Gemini (`gemini-2.5-flash`).

**Frontend:** Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Radix UI, TanStack Query, Axios, React Hook Form, Zod, Recharts, Framer Motion.

**Email:** SendLiberty (`POST https://sendliberty.com/api/send`) via connected Gmail. Optional Resend or SMTP fallback.

**Deploy:** Render Blueprint (`render.yaml`), Docker Compose, backend/frontend Dockerfiles.

---

## Project structure

```
talent-lens/
├── backend/                       FastAPI app (Render rootDir)
│   ├── app/
│   │   ├── api/routes/            auth, jobs, candidates, resumes, interviews, schedules, analytics, workflow, health
│   │   ├── core/                  config, JWT, roles, dependencies
│   │   ├── database/              async engine and session
│   │   ├── models/                SQLAlchemy models
│   │   ├── schemas/               Pydantic request/response models
│   │   ├── repositories/          data access
│   │   ├── services/              business logic and EmailService
│   │   ├── middleware/            CORS, origin guard, security headers
│   │   └── main.py                ASGI entrypoint
│   ├── ai_agents/                 LangGraph hiring graph, agents, prompts
│   ├── alembic/                   migrations 0001–0004
│   ├── scripts/seed_demo.py       local demo data
│   ├── tests/                     pytest
│   ├── requirements.txt
│   └── .env.example               copy to .env — never commit .env
├── frontend/                      Next.js app (Render rootDir)
│   ├── src/app/                   App Router pages (auth, dashboard, candidate portal)
│   ├── src/components/            UI, layout, dashboard widgets
│   ├── src/lib/api/               Axios client and resource helpers
│   └── .env.example
├── render.yaml                    Render Blueprint
├── docker-compose.yml
├── DEPLOY.md                      extra host notes
└── MVP_SYSTEM_REQUIREMENTS.md
```

---

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.12 (3.11+ works locally; Render uses 3.12.7) | `py -3 --version` |
| Node.js | 20 LTS | `node -v` |
| npm | 10+ (comes with Node 20) | `npm -v` |
| PostgreSQL | 14+ (optional locally; SQLite is the default) | `psql --version` |
| Git | 2.40+ | `git --version` |

Windows: if `py` works but `python` does not, use `py -3` in the commands below.

---

## Running locally

### 1. Clone

```powershell
git clone https://github.com/MahadCode/talent-lens.git
cd talent-lens
```

### 2. Backend

```powershell
cd backend
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
py -3 -m pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env`:

- Set `JWT_SECRET_KEY` with `openssl rand -base64 48` (or a long random string).
- For SQLite (simplest): `DATABASE_URL=sqlite+aiosqlite:///./hiring_ai.sqlite`
- For Postgres: `DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/hiring_ai`
- Set `GOOGLE_API_KEY` from [Google AI Studio](https://aistudio.google.com/apikey) (`AIza...`).
- Optional: `SENDLIBERTY_API_KEY` so verification emails actually send. Without a provider, development **logs** the message instead of sending.

```powershell
py -3 -m alembic upgrade head
py -3 -m scripts.seed_demo
py -3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: `http://localhost:8000` — docs: `http://localhost:8000/docs` (disabled when `ENVIRONMENT=production`).

### 3. Frontend

```powershell
cd frontend
copy .env.example .env.local
npm ci
npm run dev
```

Web: `http://localhost:3000`

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000/api/v1`. Restart `npm run dev` after changing env files.

### 4. Docker Compose (optional)

```powershell
$env:JWT_SECRET_KEY="long-random-secret"
$env:GOOGLE_API_KEY="AIza..."
docker compose up --build
```

### 5. Production-style local build

```powershell
cd backend
py -3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

cd frontend
npm run build
npm start
```

Seeded recruiter login (after `seed_demo` only): `recruiter@haldencapital.example` / `DemoPass123`.

---

## Environment variables

Copy `backend/.env.example` and `frontend/.env.example`. Never put real keys in git.

### Required for deployment

| Variable | Required | Used by | When | Description | Example / how to get it |
|---|---|---|---|---|---|
| `DATABASE_URL` | yes | backend runtime | runtime | SQLAlchemy URL. Render Postgres `postgres://` is rewritten to `postgresql+asyncpg://`. | Render sets this from `talent-lens-db`. Local: `postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/hiring_ai` or `sqlite+aiosqlite:///./hiring_ai.sqlite` |
| `JWT_SECRET_KEY` | yes | backend runtime | runtime | Signs access/refresh tokens. | Render can generate. Local: `openssl rand -base64 48` |
| `GOOGLE_API_KEY` | yes (parse/score) | backend runtime | runtime | Gemini key from AI Studio. Must start with `AIza`. | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `FRONTEND_URL` | yes | backend runtime | runtime | Public web origin. Used in email links and CORS. | `https://talent-lens-web.onrender.com` |
| `CORS_ALLOW_ORIGINS` | yes | backend runtime | runtime | Allowed browser origins (comma-separated, not JSON). | `https://talent-lens-web.onrender.com` |
| `ALLOWED_HOSTS` | yes | backend runtime | runtime | Host header allowlist (hostname only, no `https://`). | `talent-lens-api.onrender.com` |
| `NEXT_PUBLIC_API_BASE_URL` | yes | frontend | **build** (public-prefixed) | Browser API base, including `/api/v1`. | `https://talent-lens-api.onrender.com/api/v1` |
| `SENDLIBERTY_API_KEY` | yes on production if you use email auth | backend runtime | runtime | SendLiberty dashboard key. Connect Gmail in SendLiberty first. | Dashboard → API key (`sl_live_...`). Set on **talent-lens-api** only |
| `ENVIRONMENT` | yes (Render Blueprint) | backend runtime | runtime | `production` disables OpenAPI docs and fail-closes email if no provider. | `production` |
| `PYTHON_VERSION` | Render | backend build | build | Blueprint pin. | `3.12.7` |
| `NODE_VERSION` | Render | frontend build | build | Blueprint pin. | `20` |

### Optional

| Variable | Required | Used by | When | Description | Example / how to get it |
|---|---|---|---|---|---|
| `EMAIL_FROM` | no | backend runtime | runtime | From header. For SendLiberty, omit or use the connected Gmail. Not required if Gmail is connected. | `Talent Lens <you@gmail.com>` |
| `SL_API_KEY` | no | backend runtime | runtime | Alias for `SENDLIBERTY_API_KEY`. | same as SendLiberty key |
| `RESEND_API_KEY` | no | backend runtime | runtime | Resend fallback if SendLiberty is unset. | Resend dashboard `re_...` |
| `SMTP_HOST` | no | backend runtime | runtime | SMTP fallback. | `smtp.gmail.com` |
| `SMTP_PORT` | no | backend runtime | runtime | SMTP port. | `587` |
| `SMTP_USERNAME` | no | backend runtime | runtime | SMTP user. | your SMTP username |
| `SMTP_PASSWORD` | no | backend runtime | runtime | SMTP password. | app password, never commit |
| `JWT_ALGORITHM` | no | backend runtime | runtime | JWT algorithm. | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | backend runtime | runtime | Access token lifetime. | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | no | backend runtime | runtime | Refresh token lifetime. | `7` |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | no | backend runtime | runtime | Reset-token lifetime. | `30` |
| `UPLOAD_DIR` | no | backend runtime | runtime | Resume storage. Render free: `/tmp/uploads` (ephemeral). | `./uploads` |
| `MAX_UPLOAD_SIZE_MB` | no | backend runtime | runtime | Max PDF size. | `10` |
| `GEMINI_MODEL` | no | backend runtime | runtime | Gemini model id. | `gemini-2.5-flash` |
| `LLM_TEMPERATURE` | no | backend runtime | runtime | Agent temperature. | `0.2` |
| `EMAIL_OTP_EXPIRE_MINUTES` | no | backend runtime | runtime | OTP lifetime. | `10` |
| `EMAIL_LINK_EXPIRE_MINUTES` | no | backend runtime | runtime | Magic-link lifetime. | `30` |
| `EMAIL_OTP_MAX_ATTEMPTS` | no | backend runtime | runtime | Max OTP guesses. | `5` |
| `EMAIL_SEND_LIMIT` | no | backend runtime | runtime | Max sends per window. | `3` |
| `EMAIL_SEND_WINDOW_MINUTES` | no | backend runtime | runtime | Send-rate window. | `15` |
| `API_REWRITE_TARGET` | no | frontend | **dev runtime** | Next.js rewrite proxy if you leave `NEXT_PUBLIC_API_BASE_URL` unset locally. | `http://127.0.0.1:8000` |
| `PORT` | no | backend | runtime | Set by Render/Docker. | `8000` |

`NEXT_PUBLIC_*` values are inlined at **frontend build time**. Changing the API URL requires a **talent-lens-web** rebuild. Backend env-only changes (keys) need an API redeploy, not a web rebuild.

### Where to set them on Render

- **talent-lens-api → Environment:** `GOOGLE_API_KEY`, `SENDLIBERTY_API_KEY`, `FRONTEND_URL`, `CORS_ALLOW_ORIGINS`, `ALLOWED_HOSTS`. `DATABASE_URL` and `JWT_SECRET_KEY` come from the Blueprint. `EMAIL_FROM` is optional.
- **talent-lens-web → Environment:** `NEXT_PUBLIC_API_BASE_URL`, then **Manual Deploy** so the build picks it up.

### Deployment checklist

1. `DATABASE_URL` (Render database, or confirm Blueprint linked it)
2. `JWT_SECRET_KEY` (generate on Render if empty)
3. `GOOGLE_API_KEY` (`AIza...`)
4. `FRONTEND_URL=https://<web>.onrender.com`
5. `CORS_ALLOW_ORIGINS=https://<web>.onrender.com`
6. `ALLOWED_HOSTS=<api-host>.onrender.com`
7. `SENDLIBERTY_API_KEY` (Gmail connected in SendLiberty with send permission)
8. `NEXT_PUBLIC_API_BASE_URL=https://<api>.onrender.com/api/v1` on the **web** service, then rebuild web
9. Do not set `backend/.env` anywhere in git

---

## Running tests

```powershell
cd backend
.\venv\Scripts\Activate.ps1
py -3 -m pytest
```

Unit tests use fakes; they do not need a running Postgres or Gemini key. `pytest.ini` sets `asyncio_mode = auto`.

Frontend: `cd frontend && npm run typecheck` and `npm run lint`.

---

## API reference

Base path: `/api/v1`. Send `Authorization: Bearer <access_token>` after login.

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | liveness |
| GET | `/health/database` | DB ping |
| GET | `/health/llm` | Gemini client builds |
| GET | `/health/workflow` | LangGraph compiles |
| POST | `/auth/register` | no tokens until email is verified |
| POST | `/auth/login` | 403 `email_not_verified` or 2FA challenge |
| POST | `/auth/verify-email` | code or token |
| POST | `/auth/resend-verification` | |
| POST | `/auth/forgot-password` | |
| POST | `/auth/reset-password` | |
| POST | `/auth/refresh` | |
| GET | `/auth/me` | |
| CRUD | `/jobs`, `/candidates`, `/resumes`, `/interviews`, `/schedules`, `/users` | role-gated |
| POST | `/workflow/...` | run parse/match/score graph |
| GET | `/analytics/...` | funnel metrics |

Interactive schema: `http://localhost:8000/docs` in development.

---

## Deployment

### Render (this repo)

`render.yaml` defines **talent-lens-api** (Python), **talent-lens-web** (Node), and **talent-lens-db** (Postgres), all on the free plan.

1. Push `main` to GitHub (`https://github.com/MahadCode/talent-lens.git`).
2. Render → New → Blueprint → this repo.
3. Set the env vars in the [checklist](#deployment-checklist).
4. API start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'`
5. API build: `pip install -r requirements.txt` (rootDir `backend`)
6. Web build: `npm ci && npm run build` (rootDir `frontend`)
7. Web start: `npm start`
8. Health: `GET https://<api>.onrender.com/api/v1/health`

Free Render has **no persistent disk**. Uploads go to `/tmp/uploads` and disappear on restart.

### Docker

Backend image: `python:3.12-slim`, `alembic upgrade head && uvicorn ...`  
Frontend image: `node:20-alpine`, `NEXT_PUBLIC_API_BASE_URL` as a **build arg**, `output: "standalone"`.

---

## Git workflow

- Default branch: `main`
- Conventional Commits (`feat(auth): ...`, `fix(api): ...`, `chore(deploy): ...`)
- Do not commit `.env`, keys, or `frontend/tsconfig.tsbuildinfo`

---

## Troubleshooting

| Symptom | What to do |
|---|---|
| `Invalid email or password` | Production is empty until you register (and verify) or seed. Seeded emails do not exist on Render unless you ran seed against that database. |
| Register `503` / SendLiberty `403` insufficient scopes | Reconnect Gmail in SendLiberty and allow **Send email on your behalf**. Remove SendLiberty under [Google account permissions](https://myaccount.google.com/permissions) first so the consent screen appears again. |
| `Invalid host header` | Set `ALLOWED_HOSTS` to the API hostname (`talent-lens-api.onrender.com`). |
| CORS errors | `CORS_ALLOW_ORIGINS` must be the web origin, comma-separated, not a JSON array. |
| Gemini `429 RESOURCE_EXHAUSTED` | Free Gemini quota. Wait or use another Google AI Studio project. A new key in the **same** project does not reset the daily cap. |
| Gemini `401` | Key must start with `AIza`, not `AQ`. |
| Frontend talks to the wrong API | `NEXT_PUBLIC_API_BASE_URL` is baked in at **build**. Rebuild **talent-lens-web**. |
| `python` not found on Windows | Use `py -3`. |
| Docs `/docs` 404 in production | Expected when `ENVIRONMENT=production`. |

---

## Contributing

1. Fork or branch from `main`.
2. Keep secrets out of git. Use `.env.example` only.
3. Run `py -3 -m pytest` in `backend/` before opening a PR.

## License

MIT. See [LICENSE](LICENSE).
