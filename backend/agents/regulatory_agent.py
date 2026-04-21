import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from backend.models.schemas import RegulatoryInfo
from backend.utils.rag import retrieve_context

load_dotenv()

_client: AsyncOpenAI = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

SYSTEM_PROMPT = """You are a regulatory compliance expert for Ontario, Canada.
You MUST base your answers ONLY on the provided Official Context. If the context does not contain the answer, explicitly state that the information is unavailable. Do not rely on outside knowledge.

Given a profession, determine:
1. Whether it is a regulated profession under Ontario law
2. The governing/regulatory body (e.g., PEO, CNO, CPSO, LSO, OCT, RIBO, etc.)
3. The official URL of that governing body
4. The protected titles associated with this profession in Ontario
5. The name of the license or certificate required (if regulated)
6. A brief 2-sentence summary

Return ONLY valid JSON with this exact structure:
{
  "is_regulated": true,
  "governing_body": "Professional Engineers Ontario (PEO)",
  "governing_body_url": "https://peo.on.ca",
  "protected_titles": ["Professional Engineer", "P.Eng."],
  "license_name": "Certificate of Authorization / Licence to Practise",
  "summary": "..."
}

Focus on Ontario, Canada only. Be accurate and current."""


async def run(profession: str) -> RegulatoryInfo:
    """Determines if a profession is regulated in Ontario and returns governing body details."""
    context_text = await retrieve_context(profession)
    
    response = await get_client().chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Profession: {profession}\n\nOfficial Context:\n{context_text}"},
        ],
        temperature=0.0,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    return RegulatoryInfo(**data)
