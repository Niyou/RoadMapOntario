import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from backend.models.schemas import CertificationInfo
from backend.utils.rag import retrieve_context

load_dotenv()

_client: AsyncOpenAI = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

SYSTEM_PROMPT = """You are an Ontario professional certification expert.
You MUST base your answers ONLY on the provided Official Context. If the context does not contain the answer, explicitly state that the information is unavailable. Do not rely on outside knowledge.

Given a profession and whether it is regulated in Ontario, list:
1. Mandatory certifications / licenses required by law to practice in Ontario
2. Voluntary / optional certifications that improve employability (industry-recognized)
3. Professional licensing exams required (e.g., PPE exam for engineers, NCLEX-RN for nurses)
4. The exam bodies or organizations that administer those exams

Return ONLY valid JSON:
{
  "mandatory_certifications": ["Professional Engineer (P.Eng.) licence from PEO"],
  "voluntary_certifications": ["Project Management Professional (PMP)", "LEED Certification"],
  "professional_exams": ["Professional Practice Examination (PPE)"],
  "exam_bodies": ["Professional Engineers Ontario (PEO)", "National Council of Examiners"],
  "summary": "..."
}

Be accurate. Distinguish clearly between what is legally REQUIRED vs. what is optional but beneficial.
Focus on Ontario, Canada."""


async def run(profession: str, is_regulated: bool) -> CertificationInfo:
    """Returns mandatory vs. voluntary certification requirements for Ontario."""
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
    return CertificationInfo(**data)
