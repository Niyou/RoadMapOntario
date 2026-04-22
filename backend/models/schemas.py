from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


# ── Disambiguation ────────────────────────────────────────────────────────────

class TaxonomyMatch(BaseModel):
    profession: str
    is_regulated: bool
    regulatory_bucket: Literal[
        "RHPA",
        "FARPACTA",
        "Branch 1: DAAs",
        "Branch 2: Financial",
        "Branch 3: Direct Ministry",
        "Branch 4: Federal",
        "Branch 5: Municipal",
        "Branch 6: Crown Agencies",
        "Branch 7: Statutory",
        "Branch 8: Niche Ministries",
        "Sworn Crown Service",
        "Unregulated Free Market"
    ]
    note: str
    median_wage: Optional[str] = None


class DisambiguationResult(BaseModel):
    matches: List[TaxonomyMatch]
    error: Optional[str] = None


# ── Agent Outputs ─────────────────────────────────────────────────────────────

class RegulatoryInfo(BaseModel):
    is_regulated: bool
    governing_body: Optional[str] = None
    governing_body_url: Optional[str] = None
    protected_titles: Optional[List[str]] = None
    license_name: Optional[str] = None
    summary: str


class InstitutionInfo(BaseModel):
    name: str
    url: str

class EducationInfo(BaseModel):
    required_degree: str
    accredited_programs: Optional[List[str]] = None
    ontario_institutions: Optional[List[InstitutionInfo]] = None
    alternative_paths: Optional[List[str]] = None
    estimated_years: Optional[str] = None
    summary: str


class CertificationInfo(BaseModel):
    mandatory_certifications: Optional[List[str]] = None
    voluntary_certifications: Optional[List[str]] = None
    professional_exams: Optional[List[str]] = None
    exam_bodies: Optional[List[str]] = None
    summary: str


class ExperienceInfo(BaseModel):
    supervised_hours_required: Optional[str] = None
    internship_required: Optional[bool] = None
    ontario_experience_note: Optional[str] = None
    typical_experience_years: Optional[str] = None
    mentorship_programs: Optional[List[str]] = None
    summary: str


class RoadmapStep(BaseModel):
    step_number: int
    title: str
    description: str
    estimated_duration: Optional[str] = None
    resources: Optional[List[str]] = None


class RoadmapSummary(BaseModel):
    profession: str
    is_regulated: bool
    path_type: str          # "Regulated" | "Unregulated"
    total_estimated_years: Optional[str] = None
    steps: List[RoadmapStep]
    key_links: Optional[List[str]] = None
    important_notes: Optional[List[str]] = None


# ── Full Document (stored in MongoDB) ────────────────────────────────────────

class FullRoadmap(BaseModel):
    request_id: str
    profession: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "processing"          # "processing" | "complete" | "error"
    regulatory: Optional[RegulatoryInfo] = None
    education: Optional[EducationInfo] = None
    certification: Optional[CertificationInfo] = None
    experience: Optional[ExperienceInfo] = None
    roadmap: Optional[RoadmapSummary] = None
    error: Optional[str] = None


# ── API Request/Response ──────────────────────────────────────────────────────

class DisambiguateRequest(BaseModel):
    query: str

class AgentRequestBase(BaseModel):
    profession: str

class AgentRequestWithReg(AgentRequestBase):
    is_regulated: bool

class SummarizerRequest(AgentRequestBase):
    regulatory: RegulatoryInfo
    education: EducationInfo
    certification: CertificationInfo
    experience: ExperienceInfo
