# Talent Lens production deploy

This branch is deployment-ready. CORS, allowed hosts, HTTPS proxy headers, and origin checks read from environment variables. You only need to provide the host and domains.

Auth uses **JWT in `Authorization`**, not session cookies, so a classic CSRF token is not required. Production still rejects browser POST/PUT/PATCH/DELETE from origins outside `CORS_ALLOW_ORIGINS`.

## What you send me (fill these)

1. **Host** (pick one): `Render` (recommended), `Railway`, or `Docker VPS`
2. **Frontend domain** — example `https://hiring.yourdomain.com` or leave blank to use the host’s `*.onrender.com` URL
3. **API domain** — example `https://api.hiring.yourdomain.com` or leave blank for the host URL
4. **Gemini key** — an `AIza...` key from [Google AI Studio](https://aistudio.google.com/apikey) (paste it into the host dashboard, not into git)

I will then set the env values on that host. Do not commit `.env`.

## Architecture

```
Browser  →  Next.js (frontend)  →  FastAPI (backend)  →  Postgres
                                  ↘ Gemini (resume parse / score)
                                  ↘ disk volume (PDF uploads)
```

Two services plus a database. SQLite is local-only.

## Environment the backend expects

| Variable | Example |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | Render/Railway Postgres URL (auto-converted to `postgresql+asyncpg://`) |
| `JWT_SECRET_KEY` | long random secret (host can generate) |
| `FRONTEND_URL` | `https://YOUR_FRONTEND` |
| `CORS_ALLOW_ORIGINS` | `https://YOUR_FRONTEND` (plain URL or comma list, not JSON) |
| `ALLOWED_HOSTS` | `YOUR_API_HOST` (no `https://`; plain host or comma list) |
| `UPLOAD_DIR` | `/data/uploads` |
| `GOOGLE_API_KEY` | `AIza...` |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `SENDLIBERTY_API_KEY` | SendLiberty dashboard key (sends via connected Gmail, no domain) |
| `EMAIL_FROM` | `Talent Lens <yourgmail@gmail.com>` (the Gmail connected in SendLiberty) |
| `RESEND_API_KEY` | optional; only if you are not using SendLiberty |

## Environment the frontend expects

| Variable | Example |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://YOUR_API/api/v1` |

This is baked in at **build** time. If the API URL changes, rebuild the frontend.

## Path A — Render (recommended for this repo)

1. Push `cursor/deployment` to GitHub.
2. In Render: **New → Blueprint**, select `hackathon-web-project`, use `render.yaml`.
3. After first deploy, set on **talent-lens-api**:
   - `FRONTEND_URL=https://talent-lens-web.onrender.com`
   - `CORS_ALLOW_ORIGINS=https://talent-lens-web.onrender.com`
   - `ALLOWED_HOSTS=talent-lens-api.onrender.com`
   - `GOOGLE_API_KEY=AIza...`
   - `SENDLIBERTY_API_KEY=your-sendliberty-key`
   - `EMAIL_FROM=Talent Lens <yourgmail@gmail.com>`
4. Set on **talent-lens-web**:
   - `NEXT_PUBLIC_API_BASE_URL=https://talent-lens-api.onrender.com/api/v1`
5. Trigger a **frontend rebuild** after the API URL is set.
6. If you have a custom domain, add it in Render, then update the three URL/host vars and rebuild.

Render’s Postgres URL starts with `postgres://`; the app rewrites it to async SQLAlchemy automatically.

## Path B — Docker on a VPS

```powershell
$env:GOOGLE_API_KEY="AIza..."
$env:JWT_SECRET_KEY="long-random-secret"
$env:FRONTEND_URL="https://YOUR_DOMAIN"
$env:CORS_ALLOW_ORIGINS="https://YOUR_DOMAIN"
$env:ALLOWED_HOSTS="YOUR_DOMAIN,api.YOUR_DOMAIN"
$env:NEXT_PUBLIC_API_BASE_URL="https://api.YOUR_DOMAIN/api/v1"
docker compose up --build -d
```

Put Caddy or nginx in front for TLS. Point `YOUR_DOMAIN` at the frontend (`:3000`) and `api.YOUR_DOMAIN` at the backend (`:8000`).

## Path C — Vercel frontend + Render API

Same backend as Path A. Frontend on Vercel:

- Root directory: `frontend`
- Env: `NEXT_PUBLIC_API_BASE_URL=https://YOUR_API.onrender.com/api/v1`
- Add the Vercel URL to backend `CORS_ALLOW_ORIGINS` and `FRONTEND_URL`

## After it is live

1. Open the frontend URL → Register as recruiter
2. Verify the emailed 6-digit code (or link) before the dashboard will open
3. Create a Backend Developer job
4. Apply with a PDF (or Screening upload)
5. Confirm Gemini parse/score works (`AIza` key, not `AQ.`)
6. Dashboard counts update

New signups cannot use the app until the email is verified. Existing database users are marked verified by migration `0004_email_auth`. Two-step verification is opt-in under Settings → Security.

SendLiberty sends through the Gmail you connected in their dashboard. No domain verification. `EMAIL_FROM` should match that Gmail address.

Seed data is local-only. Production starts empty unless you run `python -m scripts.seed_demo` against that database (do not do that on a public internet app without changing `DemoPass123`).
