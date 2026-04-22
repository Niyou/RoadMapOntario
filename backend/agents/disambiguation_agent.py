import asyncio
import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from backend.models.schemas import DisambiguationResult, TaxonomyMatch
from backend.utils.jobbank import fetch_ontario_median_wage

load_dotenv()

_client: AsyncOpenAI = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

SYSTEM_PROMPT = """You are an Ontario Career Ecosystem Mapper.
Evaluate the user's query, identify the broader industry, and return exactly 6 to 8 distinct professions within that field, ranging from unregulated entry-level roles to highly regulated senior roles.

You must always return 6 to 8 related professions for the user to explore.
You must classify EVERY profession into its exact bucket. The bucket must be one of the following strictly defined options:
1. "RHPA" (Health Colleges)
2. "FARPACTA" (Trades/Engineers/Lawyers/Teachers)
3. "Branch 1: DAAs" (Real Estate, Cars, Travel)
4. "Branch 2: Financial" (FSRA, OSC)
5. "Branch 3: Direct Ministry" (Security, Paramedics)
6. "Branch 4: Federal" (Aviation, Immigration)
7. "Branch 5: Municipal" (Taxis, Holistic Spas)
8. "Branch 6: Crown Agencies" (Gaming, Cannabis)
9. "Branch 7: Statutory" (Notaries)
10. "Branch 8: Niche Ministries" (Pesticides)
11. "Sworn Crown Service" (Police, Military)
12. "Unregulated Free Market" (If it is not in the above 11, the bucket is strictly "Unregulated Free Market")

Example: If the user searches "Health", do not just return "Doctor". Return a spectrum like "Registered Nurse" (RHPA), "Paramedic" (Branch 3: Direct Ministry), "Personal Support Worker" (Unregulated Free Market), "Medical Clinic Manager" (Unregulated Free Market), etc. Totaling 6 to 8 roles.

For each match, specify:
- profession: the exact, canonical profession name used in Ontario
- is_regulated: boolean (true if regulated, false if Unregulated Free Market)
- regulatory_bucket: the exact bucket string from the list above
- note: one sentence explaining the role and what governing body applies (if any), or lack thereof

Return ONLY valid JSON with this structure:
{
  "matches": [
    {
      "profession": "...",
      "is_regulated": true/false,
      "regulatory_bucket": "...",
      "note": "..."
    }
  ],
  "error": null
}

If the query is completely unrecognizable as a profession, return:
{ "matches": [], "error": "Could not identify a matching profession. Please be more specific." }
"""


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
        matches.append(TaxonomyMatch(**m, median_wage=median_wage))

    return DisambiguationResult(
        matches=matches,
        error=data.get("error"),
    )
