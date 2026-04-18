# Paper Archive

A personal web app for collecting, analyzing, and managing research papers.

Paste an arXiv ID, arXiv/alphaXiv URL, or any paper webpage URL — the app automatically fetches metadata, generates a structured analysis with Claude, and saves everything to a cloud database.

## Features

- **Add papers** from arXiv, alphaXiv, or any webpage (e.g. transformer-circuits.pub)
- **Add multiple papers at once** — paste IDs/URLs one per line
- **AI analysis** via Claude: one-sentence summary, preliminaries, problem statement, core concept, methods & experiments, discussions & limitations, future work
- **Korean translation** of every analysis section (EN/KR toggle)
- **Keywords** (3 per paper) with click-to-filter in the archive
- **Status tracking** — Unread / Reading / Read
- **Personal notes** per paper
- **Related papers** — 3 Claude-suggested papers per entry, with arXiv links and archive badges if already saved
- **Search & filter** by title, author, keyword, status
- **Sort by date** ascending or descending
- **Relationship graph** — D3.js visualization of keyword-connected papers

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| Backend | Python + FastAPI |
| Database | Supabase (Postgres) |
| AI | Anthropic Claude API |
| Visualization | D3.js |

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Supabase](https://supabase.com) project
- [Anthropic](https://console.anthropic.com) API key

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/paper-archive.git
cd paper-archive
```

### 2. Supabase — run schema

In your Supabase project → **SQL Editor**, run the contents of [`supabase_schema.sql`](supabase_schema.sql).

### 3. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
```

`.env` contents:
```
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...
```

### 4. Frontend

```bash
cd frontend
npm install
```

### 5. Run

Double-click **`PaperArchive.command`** — both servers start and the browser opens automatically.

Or manually:
```bash
# Terminal 1
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Project Structure

```
paper-archive/
├── backend/
│   ├── app/
│   │   ├── api/papers.py          # REST endpoints
│   │   ├── core/                  # config, supabase client
│   │   ├── models/paper.py        # Pydantic models
│   │   └── services/
│   │       ├── arxiv.py           # arXiv metadata fetcher
│   │       ├── claude.py          # Claude analysis + translation
│   │       ├── papers.py          # CRUD + business logic
│   │       └── web.py             # web scraper for non-arXiv papers
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── PapersPage.tsx     # archive list + add form
│       │   ├── PaperDetailPage.tsx # full paper view
│       │   └── GraphPage.tsx      # D3 relationship graph
│       └── api.ts                 # typed Axios client
├── supabase_schema.sql
└── PaperArchive.command           # one-click launcher (macOS)
```
