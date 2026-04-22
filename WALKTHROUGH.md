# Ontario Career Compliance & Path Engine — Walkthrough 🍁

A technical walkthrough of the multi-agent AI system that maps any Ontario profession to its legal compliance and career path.

---

## What Was Built

A full-stack web application powered by **6 sequential AI agents** (GPT-4o) that takes a free-text profession query, disambiguates it to an exact Ontario profession, then runs a modular agent pipeline to produce a structured, regulation-aware career roadmap — all rendered via a glassmorphism dark-mode frontend.

---

## Project Structure

```
RoadMapOntario/
├── backend/
│   ├── main.py              # FastAPI app — routes, CORS, static serving
│   ├── orchestrator.py      # Async pipeline coordinator
│   ├── agents/
│   │   ├── disambiguation_agent.py   # Agent 0: validates & expands user input
│   │   ├── regulatory_agent.py       # Agent 1: regulated vs. unregulated
│   │   ├── education_agent.py        # Agent 2: Ontario-accredited programs
│   │   ├── certification_agent.py    # Agent 3: mandatory/voluntary certs
│   │   ├── experience_agent.py       # Agent 4: supervised hours & internships
│   │   └── summarizer_agent.py       # Agent 5: compiles final roadmap
│   ├── models/
│   │   └── schemas.py       # Pydantic models for all agent I/O
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Single-page app shell
│   ├── style.css            # Glassmorphism dark-mode design system
│   └── app.js               # Fetch-based UI logic + polling
├── .env                     # Local secrets (gitignored)
├── .env.example             # Template for required env vars
└── README.md
```

---

## Agent Pipeline

The system runs agents in two phases:

### Phase 1 — Disambiguation (synchronous, lightweight)

**`POST /api/disambiguate`** triggers `disambiguation_agent.run(query)`.

- Accepts raw free-text (e.g., `"nurse"`, `"engineer"`)
- Returns 3–5 canonical Ontario profession options with category (`Regulated` / `Unregulated`) and a one-line note
- No background task — just a direct GPT-4o call
- Used by the frontend to let the user pick the exact profession before committing

### Phase 2 — Parallel/Modular Agent Pipeline (async)

**`POST /api/agent/...`** endpoints are called by the frontend:

1. Frontend initiates independent POST requests to `regulatory`, `education`, `certification`, and `experience` endpoints simultaneously.
2. Agents run independently and return their respective JSON payloads.
3. The frontend aggregates all payloads and makes a final POST request to `summarize`.

| # | Agent | Output Schema | Key Fields |
|---|-------|--------------|------------|
| 1 | **Regulatory** | `RegulatoryInfo` | `is_regulated`, `governing_body`, `governing_body_url`, `protected_titles`, `license_name` |
| 2 | **Education** | `EducationInfo` | `required_degree`, `accredited_programs`, `ontario_institutions`, `estimated_years` |
| 3 | **Certification** | `CertificationInfo` | `mandatory_certifications`, `voluntary_certifications`, `professional_exams` |
| 4 | **Experience** | `ExperienceInfo` | `supervised_hours_required`, `internship_required`, `typical_experience_years` |
| 5 | **Summarizer** | `RoadmapSummary` | `steps[]`, `path_type`, `total_estimated_years`, `key_links`, `important_notes` |

All outputs are strictly defined using Pydantic schemas.

### Branching Logic (Summarizer)

The Summarizer agent adapts its output based on `is_regulated`:

- **Regulated path** → 4 steps: Accredited Education → Supervised Experience → Professional Exam → Licence & Practice
- **Unregulated path** → 3 steps: Relevant Education → Skill Certifications → Portfolio / Job Search

---

## Data Layer

The system is entirely stateless. The frontend maintains the application state and aggregates the JSON data from the backend agents. No database is used.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/disambiguate` | Returns 3–5 matched Ontario professions for user selection |
| `POST` | `/api/agent/...` | 5 distinct endpoints (`regulatory`, `education`, `certification`, `experience`, `summarize`) |
| `GET` | `/api/health` | Health check |
| `GET` | `/` | Serves `frontend/index.html` |

---

## Frontend

Single-page app (`frontend/`) served directly by FastAPI via `StaticFiles`.

**Design**: Glassmorphism dark-mode with backdrop blur, gradient accents, and smooth transitions.

**Flow**:
1. User types a profession → hits Search
2. `POST /api/disambiguate` → disambiguation cards rendered
3. User selects a profession → Frontend displays agent dashboard
4. Frontend triggers agents independently
5. On all agents complete, User clicks Compile Final Roadmap
6. Cards visually branch based on `path_type` (Regulated vs. Unregulated)

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key — all agents use `gpt-4o` with `response_format: json_object` |

Copy `.env.example` → `.env` and populate both values before running.

---

## Running Locally

```bash
# 1. Clone and set up environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Start the server (from project root)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000) — the frontend is served automatically.

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Key Design Decisions

- **`response_format: json_object`** on all GPT-4o calls ensures agent outputs are always parseable without prompt hacking
- **Stateless backend** keeps the system highly modular and performant. The frontend orchestrates the agent requests directly without maintaining an intermediate database state.
- **Pydantic schemas** enforce a strict contract between agent outputs, catching malformed AI responses before they reach the frontend.
