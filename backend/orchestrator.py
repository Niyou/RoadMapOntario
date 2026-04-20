import asyncio
import uuid
from datetime import datetime

from backend.agents import (
    regulatory_agent,
    education_agent,
    certification_agent,
    experience_agent,
    summarizer_agent,
)
from backend.db import mongo


async def run_pipeline(profession: str) -> str:
    """
    Orchestrates the 5-agent pipeline for a given confirmed profession.
    Writes incremental updates to MongoDB and returns the request_id.
    """
    request_id = str(uuid.uuid4())

    # Initialize the document in MongoDB
    await mongo.save_roadmap(request_id, {
        "request_id": request_id,
        "profession": profession,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "processing",
    })

    # Run agents asynchronously in the background
    asyncio.create_task(_run_agents(request_id, profession))

    return request_id


async def _run_agents(request_id: str, profession: str) -> None:
    """Internal: runs all agents sequentially, saving results to MongoDB."""
    try:
        # ── Agent 1: Regulatory ───────────────────────────────────────────────
        regulatory = await regulatory_agent.run(profession)
        await mongo.save_roadmap(request_id, {
            "regulatory": regulatory.model_dump(),
        })

        is_regulated = regulatory.is_regulated

        # ── Agent 2: Education ────────────────────────────────────────────────
        education = await education_agent.run(profession, is_regulated)
        await mongo.save_roadmap(request_id, {
            "education": education.model_dump(),
        })

        # ── Agent 3: Certification ────────────────────────────────────────────
        certification = await certification_agent.run(profession, is_regulated)
        await mongo.save_roadmap(request_id, {
            "certification": certification.model_dump(),
        })

        # ── Agent 4: Experience ───────────────────────────────────────────────
        experience = await experience_agent.run(profession, is_regulated)
        await mongo.save_roadmap(request_id, {
            "experience": experience.model_dump(),
        })

        # ── Agent 5: Summarizer ───────────────────────────────────────────────
        roadmap = await summarizer_agent.run(
            profession, regulatory, education, certification, experience
        )
        await mongo.save_roadmap(request_id, {
            "roadmap": roadmap.model_dump(),
            "status": "complete",
        })

    except Exception as exc:
        await mongo.update_status(request_id, status="error", error=str(exc))
        raise
