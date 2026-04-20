import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.agents import disambiguation_agent
from backend.models.schemas import (
    DisambiguateRequest, SearchRequest, SearchResponse,
    DisambiguationResult,
)
from backend.db import mongo
from backend import orchestrator

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
    Fast and lightweight — no MongoDB write, no agents spawned yet.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result = await disambiguation_agent.run(req.query.strip())
    return result


@app.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    """
    Phase 2: Start the 5-agent pipeline for a confirmed profession.
    Returns a request_id immediately; pipeline runs in background.
    """
    if not req.profession.strip():
        raise HTTPException(status_code=400, detail="Profession cannot be empty.")

    request_id = await orchestrator.run_pipeline(req.profession.strip())
    return SearchResponse(request_id=request_id)


@app.get("/api/roadmap/{request_id}")
async def get_roadmap(request_id: str):
    """
    Poll this endpoint to check pipeline status and retrieve the full roadmap.
    Status values: 'processing' | 'complete' | 'error'
    """
    doc = await mongo.get_roadmap(request_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Roadmap not found.")
    return doc


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
