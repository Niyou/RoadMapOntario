import asyncio
import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from backend.models.schemas import DisambiguationResult, ProfessionMatch
from backend.utils.jobbank import fetch_ontario_median_wage

load_dotenv()

_client: AsyncOpenAI = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

SYSTEM_PROMPT = """You are an Ontario, Canada career expert.
Given a user's raw input, return 3 to 5 Ontario professions using this strategy:

1. EXACT MATCH FIRST: Include the closest match to what the user typed.
2. RELATED PROFESSIONS: Also include adjacent roles in the same field at different 
   levels or specializations. Examples:
   - "pharmacist" → also include "Pharmacy Technician", "Pharmacy Assistant"
   - "nurse" → also include "Registered Practical Nurse", "Nurse Practitioner"
   - "engineer" → also include "Engineering Technologist", "Engineering Technician"
   - "doctor" → also include "Physician Assistant", "Nurse Practitioner"
   - "lawyer" → also include "Paralegal", "Law Clerk"
   - "teacher" → also include "Early Childhood Educator", "Educational Assistant"
   This helps users discover stepping-stone or alternative paths they may not know about.

For each match, specify:
- profession: the exact, canonical profession name used in Ontario
- category: "Regulated" or "Unregulated" (based on Ontario law)
- note: one sentence explaining the role and what governing body applies (if any)

Return ONLY valid JSON with this structure:
{
  "matches": [
    { "profession": "...", "category": "Regulated|Unregulated", "note": "..." }
  ],
  "error": null
}

If the query is completely unrecognizable as a profession, return:
{ "matches": [], "error": "Could not identify a matching profession. Please be more specific." }

Focus strictly on Ontario, Canada. Be accurate about regulation status."""


async def run(query: str) -> DisambiguationResult:
    """
    Takes raw user text, returns a list of matched Ontario professions to choose from.
    Concurrently fetches Ontario median wages from Job Bank for each match.
    """
    response = await get_client().chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"User query: {query}"},
        ],
        temperature=0.2,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    raw_matches = data.get("matches", [])
    if not raw_matches:
        return DisambiguationResult(matches=[], error=data.get("error"))

    # Fetch Ontario median wages from Job Bank concurrently for all matches
    wages = await asyncio.gather(
        *[fetch_ontario_median_wage(m["profession"]) for m in raw_matches],
        return_exceptions=True,
    )

    matches = []
    for m, wage in zip(raw_matches, wages):
        median_wage = wage if isinstance(wage, str) else None
        matches.append(ProfessionMatch(**m, median_wage=median_wage))

    return DisambiguationResult(
        matches=matches,
        error=data.get("error"),
    )
