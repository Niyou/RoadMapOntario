import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from backend.models.schemas import EducationInfo

load_dotenv()

_client: AsyncOpenAI = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

SYSTEM_PROMPT = """You are an Ontario education expert specializing in post-secondary pathways.
Given a profession and whether it is regulated in Ontario, provide:
1. The required degree or educational credential
2. Ontario-accredited programs (for regulated) OR industry-preferred credentials (for unregulated)
3. Ontario institutions that offer relevant programs (AT LEAST 6 to 10 institutions, e.g., U of T, McMaster, Humber, Seneca, etc.), including official website URLs for each institution or program.
4. Alternative pathways (college diplomas, bridging programs, internationally educated professionals paths)
5. Estimated years of education required

Return ONLY valid JSON:
{
  "required_degree": "Bachelor of Engineering (Civil)",
  "accredited_programs": ["Canadian Engineering Accreditation Board (CEAB) accredited programs"],
  "ontario_institutions": [
    {"name": "University of Toronto", "url": "https://discover.engineering.utoronto.ca/"},
    {"name": "McMaster University", "url": "https://www.eng.mcmaster.ca/"},
    {"name": "Ryerson University", "url": "https://www.torontomu.ca/"}
  ],
  "alternative_paths": ["Internationally Educated Engineers bridging program at Centennial College"],
  "estimated_years": "4 years",
  "summary": "..."
}

Focus strictly on Ontario, Canada institutions and programs."""


async def run(profession: str, is_regulated: bool) -> EducationInfo:
    """Returns Ontario-specific education requirements for the given profession."""
    context = "This is a REGULATED profession in Ontario." if is_regulated \
        else "This is an UNREGULATED profession in Ontario."

    response = await get_client().chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Profession: {profession}\nContext: {context}"},
        ],
        temperature=0.1,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    return EducationInfo(**data)
