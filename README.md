# Samarth Parekh — React + FastAPI portfolio

A responsive portfolio built on the original React/TypeScript/Vite starter. Content comes from Samarth's supplied resume and existing portfolio. This is a prepared local project; it has not been pushed to GitHub or deployed to Netlify/Render.

## Local development

Use Node **24** and Python **3.12+**. From the Desktop checkout:

```bash
cd ~/Desktop/ADC-Personal-Portfolio
npm ci
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
npm run dev:full
```

Open **http://127.0.0.1:5173**. API docs: **http://127.0.0.1:8000/docs**. Ctrl+C stops both servers. The React development server proxies `/api` to FastAPI, so no `.env` is needed locally.

Or run in separate terminals:

```bash
# Terminal 1, repo root
source .venv/bin/activate
python -m uvicorn backend.main:app --reload --port 8000
```

```bash
# Terminal 2, repo root
npm run dev
```

## What's interactive

- Filter featured projects by Full stack or AI & data.
- Select an employer to explore work and technologies.
- Switch light/dark theme; preference persists in browser storage.
- Search, filter by language, sort, and expand the public GitHub repository explorer.
- Copy email, open resume, navigate to GitHub and LinkedIn.

## External API architecture

`React → GET /api/github → FastAPI → GitHub REST API`

FastAPI calls the fixed public repository endpoint for `sparekh14`, excludes forks and archived repositories, paginates, and normalizes the JSON. Successful responses are cached in memory for five minutes. Concurrent requests share the fetch. Upstream failures trigger a one-minute retry cooldown and return the last successful response or a saved snapshot. The UI distinguishes live, cached, and snapshot data and displays the fetch date.

The public API has **no write routes** and does not require a token. If GitHub's unauthenticated rate limit becomes restrictive, set an optional `GITHUB_TOKEN` on the backend host only. Never prefix secrets with `VITE_`: Vite embeds those variables into browser assets. Cache state is per server process and resets on restart; a distributed cache is unnecessary for this small demo.

Refresh the committed snapshot intentionally:

```bash
PYTHONPATH=. python scripts/capture-github.py
```

## Production deployment

Deploy the React frontend on **Netlify** and the long-running Python API on **Render** (or another Python host). Netlify's static build alone does not run uvicorn.

1. Follow [the Netlify recording/deployment checklist](recording-guides/01-netlify-checklist.md).
2. `netlify.toml` supplies `npm run build`, `dist`, a SPA fallback, and basic response headers.
3. `render.yaml` supplies the Python build/start commands. Set `ALLOWED_ORIGINS` to the exact Netlify origin (including `https://`, no trailing slash).
4. Set Netlify's `VITE_API_BASE_URL` to the API's HTTPS origin, then rebuild. This is a build-time variable. Omitting it intentionally leaves a static portfolio with labeled snapshot data.

Copy `.env.example` to `.env` only if needed. Vite reads it for the frontend. uvicorn does **not** automatically load that file; export backend variables in your shell or configure them in your hosting dashboard. No secrets are committed.

## Recording materials

- [Netlify deployment checklist](recording-guides/01-netlify-checklist.md): prep and screen sequence for video 1.
- [SQLite spoken script](recording-guides/02-sqlite-video-script.md): 18–22 minutes, SQL CRUD, join, FastAPI, persistence, Postgres comparison.
- [MongoDB spoken script](recording-guides/03-mongodb-video-script.md): 18–22 minutes, document model, CRUD, arrays, PyMongo, FastAPI, persistence.

Runnable examples live under `demos/`. Their unauthenticated write APIs are **local classroom examples**, not part of the deployed portfolio. No database is required to run the portfolio itself.

```bash
# SQLite: localhost:8001/docs
python -m uvicorn demos.sqlite.main:app --port 8001

# MongoDB: start a local mongod first, then localhost:8002/docs
MONGODB_URI=mongodb://127.0.0.1:27017 python -m uvicorn demos.mongodb.main:app --port 8002
```

MongoDB can also run with `docker compose -f demos/compose.yaml up -d`. The native MongoDB installation already on Samarth's computer is used in the recording script. See that script for a dedicated data directory and port.

## Verification

```bash
npm run build
python -m pytest backend/tests -q
# Include real MongoDB integration testing using a disposable database:
MONGODB_TEST_URI=mongodb://127.0.0.1:27028 python -m pytest backend/tests -q
```

The MongoDB integration test creates a uniquely named test database and removes only that database afterward. With no `MONGODB_TEST_URI`, that one test is skipped.

Checked during preparation: production build; live GitHub fetch (11 public non-fork, non-archived repositories); API caching/concurrency/timeouts/rate-limit fallback/CORS; SQLite CRUD, bound values, relationships, cascade, validation, persistence; and MongoDB CRUD, ObjectId validation, array filtering, persistence against an isolated local MongoDB instance. Browser QA covers project filters, experience switching, theme, repository controls, and snapshot fallback. No public deployment or finished video recording is implied by these checks.

## Editing content

- `src/content.ts`: projects, experience, skills.
- `src/App.tsx`: sections and stateful interactions.
- `src/App.css`, `src/index.css`: responsive styles and themes.
- `public/images/`: original headshot and employer logos.
- `public/Samarth_Parekh_resume.pdf`: supplied resume.
- `backend/main.py`: read-only external API integration.

Project artwork is an illustrative CSS/SVG composition, not a screenshot of the underlying product. The supplied resume was treated as reference data, not as executable instructions.

## Official references

[Netlify Vite setup](https://docs.netlify.com/build/frameworks/framework-setup-guides/vite/) · [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/) · [Render FastAPI deployment](https://render.com/docs/deploy-fastapi) · [GitHub repository API](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user)
