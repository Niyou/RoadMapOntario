import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from backend.models.schemas import ExperienceInfo
from backend.utils.rag import retrieve_context

load_dotenv()

_client: AsyncOpenAI = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

SYSTEM_PROMPT = """You are an Ontario workforce integration expert.
You MUST base your answers ONLY on the provided Official Context. If the context does not contain the answer, explicitly state that the information is unavailable. Do not rely on outside knowledge.

Given a profession and whether it is regulated in Ontario, outline:
1. Required supervised work hours (if any — e.g., 48 months for P.Eng.)
2. Whether a formal internship or co-op is required or strongly recommended
3. Any Ontario-specific experience requirements (e.g., "Ontario experience" noted by employers)
4. Typical total years of experience needed before full licensure or employability
5. Mentorship programs available in Ontario for this profession

Return ONLY valid JSON:
{
  "supervised_hours_required": "48 months of acceptable engineering experience",
  "internship_required": true,
  "ontario_experience_note": "PEO requires experience references from licensed P.Engs in Ontario",
  "typical_experience_years": "4 years post-graduation",
  "mentorship_programs": ["Ontario Society of Professional Engineers (OSPE) mentorship", "PEO PEAK Program"],
  "summary": "..."
}

Focus specifically on Ontario, Canada requirements."""


async def run(profession: str, is_regulated: bool) -> ExperienceInfo:
    """Returns supervised experience and Ontario-specific work requirements."""
    context_text = await retrieve_context(profession)

    context = "This is a REGULATED profession in Ontario." if is_regulated \
        else "This is an UNREGULATED profession in Ontario."

    response = await get_client().chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Profession: {profession}\nContext: {context}\n\nOfficial Context:\n{context_text}"},
        ],
        temperature=0.0,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    return ExperienceInfo(**data)
