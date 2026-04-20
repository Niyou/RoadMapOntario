# Ontario Career Compliance & Path Engine 🍁

A multi-agent AI web application that identifies the exact legal and professional path for any given profession in Ontario, Canada. It distinguishes between **Regulated** and **Unregulated** careers and provides a step-by-step visual roadmap.

---

## Architecture

```
User Input → Disambiguation Agent (GPT-4o)
                ↓ (user picks profession)
          Regulatory Agent → Education Agent → Certification Agent
                                                      ↓
          Experience Agent → Summarizer Agent → MongoDB
                                                      ↓
                                              Visual Roadmap (Frontend)
```

## Setup

### 1. Clone & configure environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and MONGO_URI
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
| `POST` | `/api/search` | Starts the 5-agent pipeline for a confirmed profession |
| `GET`  | `/api/roadmap/{request_id}` | Polls for and retrieves the full career roadmap |
| `GET`  | `/api/health` | Health check |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key (GPT-4o) |
| `MONGO_URI` | MongoDB Atlas connection string |

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

- **Backend**: FastAPI + async Motor (MongoDB)
- **AI**: OpenAI GPT-4o with `response_format: json_object`
- **Frontend**: Vanilla HTML/CSS/JS — glassmorphism dark-mode design
- **Database**: MongoDB (stores each roadmap by `request_id`)
