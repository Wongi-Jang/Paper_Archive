# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload          # dev server on :8000
pip install -r requirements.txt        # install deps
```

### Frontend
```bash
cd frontend
npm run dev      # dev server on :5173
npm run build    # tsc + vite build
```

### Run both together
```bash
./start.sh       # or double-click PaperArchive.command on macOS
```

### Backend environment
`backend/.env` (copy from `.env.example`):
```
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...
```
Optional: `ALLOWED_ORIGINS=https://your-domain.com` for extra CORS origins.

### Database
Run `supabase_schema.sql` in the Supabase SQL Editor once to create the `papers` table. The `analysis` column is `jsonb`; an index on `analysis->'keywords'` supports keyword filtering.

---

## Architecture

### Data flow for adding a paper
1. User pastes an arXiv ID, arXiv/alphaXiv URL, or any web URL into the frontend.
2. `POST /api/papers/` hits `app/api/papers.py` → `services/papers.py::add_paper`.
3. `services/web.py::_detect_source` classifies input as `arxiv` or `web`.
   - `arxiv`: `services/arxiv.py::fetch_paper_metadata` calls the arXiv API.
   - `web`: `services/web.py::fetch_web_paper` scrapes the page (raw text ≤ 6000 chars).
4. `services/claude.py::analyze_paper` makes **two sequential synchronous Claude calls** (model `claude-sonnet-4-6`):
   - First call: English structured analysis + keywords + 3 suggested related papers → JSON.
   - Second call: Korean translation of the same fields (keywords excluded).
5. Row is inserted into Supabase `papers` table with `analysis` stored as JSONB.

### Backend layout
```
backend/app/
├── main.py            # FastAPI app, CORS, router mount at /api
├── api/papers.py      # REST endpoints
├── core/
│   ├── config.py      # pydantic-settings: reads .env
│   └── supabase.py    # singleton Supabase client
├── models/paper.py    # Pydantic models (Paper, PaperAnalysis, RelatedPaper, …)
└── services/
    ├── arxiv.py       # arXiv XML API fetcher
    ├── claude.py      # Anthropic client, analysis + translation prompts
    ├── papers.py      # CRUD + business logic, _row_to_paper, _build_analysis_row
    └── web.py         # _detect_source, HTML scraper for non-arXiv URLs
```

### Frontend layout
```
frontend/src/
├── api.ts             # typed Axios client + all TypeScript interfaces (Paper, PaperAnalysis, …)
├── App.tsx            # React Router routes: / → PapersPage, /:id → PaperDetailPage, /graph → GraphPage
└── pages/
    ├── PapersPage.tsx        # paper list, search/filter by keyword/status, bulk-add form
    ├── PaperDetailPage.tsx   # full analysis view, EN/KR toggle, notes, related papers
    └── GraphPage.tsx         # D3.js force-directed graph of keyword-connected papers
```

No state management library — the app uses React Query (`@tanstack/react-query`) for server state and local `useState` for UI state.

### Key design decisions
- **`arxiv_id` is the unique key** for deduplication; for web-scraped papers the full URL is used as the `arxiv_id`.
- **`analysis` is a flat JSONB blob** in Postgres — all English and Korean fields are stored in one column. `_build_analysis_row` / `_row_to_paper` handle serialisation.
- **Claude calls are synchronous** (not async) because the `anthropic` Python SDK's async client is not used; `analyze_paper` is declared `async` but blocks internally.
- **Related papers** are fetched lazily on demand via `GET /api/papers/:id/related`; the endpoint resolves each `suggested_related` arxiv ID against the archive and falls back to a live arXiv lookup.
- **`source` field** (`arxiv` | `web`) tracks how a paper was ingested; web papers have no `pdf_url` and pass raw scraped text to Claude instead of a structured abstract.
