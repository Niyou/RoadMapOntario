import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.agents import (
    disambiguation_agent,
    regulatory_agent,
    education_agent,
    certification_agent,
    experience_agent,
    summarizer_agent
)
from backend.models.schemas import (
    DisambiguateRequest, DisambiguationResult,
    AgentRequestBase, AgentRequestWithReg, SummarizerRequest,
    RegulatoryInfo, EducationInfo, CertificationInfo, ExperienceInfo, RoadmapSummary
)

app = FastAPI(
    title="Ontario Career Compliance & Path Engine",
    description="Multi-agent system that maps any Ontario profession to its legal compliance path.",
    version="1.0.0",
)

# ── CORS (allow frontend dev server) ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── API Routes ────────────────────────────────────────────────────────────────

@app.post("/api/disambiguate", response_model=DisambiguationResult)
async def disambiguate(req: DisambiguateRequest):
    """
    Phase 1: Validate raw user input and return 3–5 Ontario profession options.
    Fast and lightweight — no agents spawned yet.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result = await disambiguation_agent.run(req.query.strip())
    return result


@app.post("/api/agent/regulatory", response_model=RegulatoryInfo)
async def run_regulatory(req: AgentRequestBase):
    if not req.profession.strip():
        raise HTTPException(status_code=400, detail="Profession cannot be empty.")
    return await regulatory_agent.run(req.profession.strip())

@app.post("/api/agent/education", response_model=EducationInfo)
async def run_education(req: AgentRequestWithReg):
    if not req.profession.strip():
        raise HTTPException(status_code=400, detail="Profession cannot be empty.")
    return await education_agent.run(req.profession.strip(), req.is_regulated)

@app.post("/api/agent/certification", response_model=CertificationInfo)
async def run_certification(req: AgentRequestWithReg):
    if not req.profession.strip():
        raise HTTPException(status_code=400, detail="Profession cannot be empty.")
    return await certification_agent.run(req.profession.strip(), req.is_regulated)

@app.post("/api/agent/experience", response_model=ExperienceInfo)
async def run_experience(req: AgentRequestWithReg):
    if not req.profession.strip():
        raise HTTPException(status_code=400, detail="Profession cannot be empty.")
    return await experience_agent.run(req.profession.strip(), req.is_regulated)

@app.post("/api/agent/summarize", response_model=RoadmapSummary)
async def run_summarize(req: SummarizerRequest):
    if not req.profession.strip():
        raise HTTPException(status_code=400, detail="Profession cannot be empty.")
    return await summarizer_agent.run(
        req.profession.strip(),
        req.regulatory,
        req.education,
        req.certification,
        req.experience
    )


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "Ontario Career Path Engine"}


# ── Serve Frontend ────────────────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
