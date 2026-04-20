import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from backend.models.schemas import (
    RoadmapSummary, RoadmapStep,
    RegulatoryInfo, EducationInfo, CertificationInfo, ExperienceInfo
)

load_dotenv()

_client: AsyncOpenAI = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

SYSTEM_PROMPT = """You are a career path architect for Ontario, Canada.
You will receive structured data from 4 specialist agents. Compile this into a clear, 
chronological career roadmap for the user.

OUTPUT FORMAT:
- If REGULATED: produce 4 steps: (1) Accredited Education, (2) Supervised Experience, 
  (3) Professional Exam / Application, (4) Licence & Practice
- If UNREGULATED: produce 3 steps: (1) Relevant Education, (2) Skill Certifications, 
  (3) Portfolio / Project Building & Job Search

Each step must include:
- step_number (int)
- title (short, max 6 words)
- description (2-3 sentences, specific and actionable)
- estimated_duration (e.g., "4 years", "6–12 months")
- resources (list of 1–3 relevant URLs or organization names)

Also include:
- total_estimated_years: total career path duration
- key_links: top 3 official Ontario resources (governing body, job board, etc.)
- important_notes: any critical Ontario-specific caveats (e.g., IEN bridging, HRSDC)

Return ONLY valid JSON:
{
  "profession": "...",
  "is_regulated": true,
  "path_type": "Regulated",
  "total_estimated_years": "8-10 years",
  "steps": [...],
  "key_links": [...],
  "important_notes": [...]
}"""


async def run(
    profession: str,
    regulatory: RegulatoryInfo,
    education: EducationInfo,
    certification: CertificationInfo,
    experience: ExperienceInfo,
) -> RoadmapSummary:
    """Compiles all agent outputs into a structured Ontario career roadmap."""

    context = f"""
PROFESSION: {profession}

--- REGULATORY DATA ---
{regulatory.model_dump_json(indent=2)}

--- EDUCATION DATA ---
{education.model_dump_json(indent=2)}

--- CERTIFICATION DATA ---
{certification.model_dump_json(indent=2)}

--- EXPERIENCE DATA ---
{experience.model_dump_json(indent=2)}
"""

    response = await get_client().chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        temperature=0.2,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    steps = [RoadmapStep(**s) for s in data.get("steps", [])]
    return RoadmapSummary(
        profession=data["profession"],
        is_regulated=data["is_regulated"],
        path_type=data["path_type"],
        total_estimated_years=data.get("total_estimated_years"),
        steps=steps,
        key_links=data.get("key_links"),
        important_notes=data.get("important_notes"),
    )
