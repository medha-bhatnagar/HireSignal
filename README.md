

https://github.com/user-attachments/assets/136c03d0-3263-45e3-bee7-51ed94b54e34

# HireSignal

A Chrome extension that generates an AI summary of any GitHub profile and scores how well that
developer matches a pasted job description — built to help recruiters and hiring managers get a
quick, structured read on a candidate's public GitHub activity.





## What it does

- **AI Profile Summary** — one click on any GitHub profile generates a plain-language summary of
  the developer's experience level, primary technologies, and technical strengths.
- **Job Match** — paste in a job description and get a match assessment scoring that developer
  against the role's requirements.
- **PDF export** — either result can be exported as a PDF report.
- **Optional GitHub sign-in** — using the extension anonymously works out of the box; signing in
  raises your rate limit and uses your own GitHub API quota instead of a shared one.

## Why this project exists

This started as a working extension and became a deliberate exercise in applying real backend
system-design concepts on top of it — not just calling an LLM API, but building the infrastructure
a production system around an AI feature actually needs:

- **Authentication** — hand-rolled GitHub OAuth (not a library), issuing short-lived JWTs from a
  Django backend, with a background service worker handling the OAuth popup so it survives Chrome
  tearing down the extension popup mid-flow.
- **Two-tier rate limiting** — a lower limit for anonymous users, a higher one for signed-in users,
  enforced with database-backed fixed-window counters.
- **Caching** — profile analyses and job-match results are cached (Django's cache framework,
  database-backed), so repeat lookups of the same profile or job description cost zero additional
  LLM tokens or GitHub API calls.
- **Encrypted credential storage** — each signed-in user's personal GitHub access token is
  encrypted at rest (Fernet symmetric encryption), never exposed back to the client.
- **Real budget analysis** — the LLM provider's token-per-day limit, not its request-count limit,
  turned out to be the actual bottleneck once real per-request token usage was measured against it.

## Architecture

```
Chrome Extension (React + TypeScript, Manifest V3)
  ├── Popup UI          — state machine driving Home / Loading / Result / Error screens
  ├── Background worker  — owns the GitHub OAuth flow (chrome.identity)
  └── lib/               — auth + backend API client, kept separate from UI components
        │
        │  HTTPS (JWT or anonymous device ID)
        ▼
Django Backend
  ├── accounts/    — GitHub OAuth code-exchange, JWT issuance
  ├── clients/     — optional-auth decorator (anonymous OR signed-in, never blocked)
  ├── common/      — rate limiting, search history, field-level encryption
  ├── cache/       — cache-aside helper (Django DatabaseCache backend)
  ├── developers/  — GitHub data fetching + AI summary generation
  └── jobs/        — job-match result storage
        │
        ▼
GitHub API (per-user or shared token) + Groq (LLM inference)
```

## Tech stack

- **Frontend**: React, TypeScript, Vite, Chrome Extension Manifest V3
- **Backend**: Django, Django REST Framework, `djangorestframework-simplejwt`
- **Database**: SQLite (dev) — Postgres migration in progress for production use
- **AI**: Groq (`openai/gpt-oss-120b`)
- **Security**: Fernet field-level encryption for stored GitHub tokens

## Running it locally

You'll need your own API keys — none are distributed with this repo (see `.env.example`).

**Backend:**
```bash
cd backend/dashboard_project
python3 -m venv venv
source venv/bin/acti

https://github.com/user-attachments/assets/de3c571d-7eb1-4fbe-8f82-93454b59cdca

vate
pip install -r requirements.txt
cp .env.example .env   # fill in GITHUB_TOKEN, GROQ_API_KEY, GITHUB_CLIENT_ID/SECRET, FIELD_ENCRYPTION_KEY
python manage.py migrate
python manage.py createcachetable
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
# set GITHUB_CLIENT_ID in src/lib/config.ts
npm run build
```

Then load `frontend/dist` as an unpacked extension via `chrome://extensions` (Developer mode →
Load unpacked). If you want GitHub sign-in working, register a GitHub OAuth App with the callback
URL `https://<your-extension-id>.chromiumapp.org/`.

## Known limitations / what's next
 
- SQLite is fine for local development but not for concurrent production traffic — a Postgres
  migration is planned before any real deployment.
- Sign-out clears local credentials but doesn't yet revoke the JWT server-side (no token
  blacklist implemented yet).
- Not deployed publicly — see the demo above, or run it locally with your own API keys.
