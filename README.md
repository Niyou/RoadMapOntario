# Ontario Career Compliance & Path Engine 🍁

A multi-agent AI web application that identifies the exact legal and professional path for any given profession in Ontario, Canada. It distinguishes between **Regulated** and **Unregulated** careers and provides a step-by-step visual roadmap.

---

## Architecture

```
User Input → Disambiguation Agent (GPT-4o)
                ↓ (user picks profession)
          Regulatory Agent → Education Agent → Certification Agent
                                                      ↓
          Experience Agent → Summarizer Agent → Frontend
                                                      ↓
                                              Visual Roadmap
```

## Setup

### 1. Clone & configure environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Create virtual environment and install dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the development server

```bash
# From the project root
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/disambiguate` | Validates input, returns 3–5 Ontario profession options |
| `POST` | `/api/agent/regulatory` | Determines regulatory status and governing body |
| `POST` | `/api/agent/education` | Returns education requirements and accredited programs |
| `POST` | `/api/agent/certification` | Returns mandatory vs. voluntary certifications |
| `POST` | `/api/agent/experience` | Returns required supervised experience |
| `POST` | `/api/agent/summarize` | Compiles results into a final roadmap |
| `GET`  | `/api/health` | Health check |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key (GPT-4o) |

---

## Multi-Agent Pipeline

1. **Disambiguation Agent** — Validates free-text input, returns canonical Ontario profession options
2. **Regulatory Agent** — Determines regulated vs. unregulated status, governing body (PEO, CNO, etc.), protected titles
3. **Education Agent** — Ontario-accredited programs or industry-preferred credentials 
4. **Certification Agent** — Mandatory licences vs. voluntary certifications and professional exams
5. **Experience Agent** — Supervised hours, Ontario-specific experience, mentorship programs
6. **Summarizer Agent** — Compiles chronological career path with timelines and resources

---

## Branching Logic

- **Regulated**: Accredited Degree → Supervised Experience → Professional Exam → Licence
- **Unregulated**: Relevant Education → Skill Certifications → Portfolio Building

---

## Tech Stack

- **Backend**: FastAPI
- **AI**: OpenAI GPT-4o with `response_format: json_object`
- **Frontend**: Vanilla HTML/CSS/JS — glassmorphism dark-mode design
