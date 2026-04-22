from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Any
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
    governing_body: Optional[Any] = None
    governing_body_url: Optional[Any] = None
    protected_titles: Optional[Any] = None
    license_name: Optional[Any] = None
    summary: str


class InstitutionInfo(BaseModel):
    name: str
    url: str

class EducationInfo(BaseModel):
    required_degree: str
    accredited_programs: Optional[Any] = None
    ontario_institutions: Optional[Any] = None
    alternative_paths: Optional[Any] = None
    estimated_years: Optional[Any] = None
    summary: str


class CertificationInfo(BaseModel):
    mandatory_certifications: Optional[Any] = None
    voluntary_certifications: Optional[Any] = None
    professional_exams: Optional[Any] = None
    exam_bodies: Optional[Any] = None
    summary: str


class ExperienceInfo(BaseModel):
    supervised_hours_required: Optional[Any] = None
    internship_required: Optional[Any] = None
    ontario_experience_note: Optional[Any] = None
    typical_experience_years: Optional[Any] = None
    mentorship_programs: Optional[Any] = None
    summary: str


class RoadmapStep(BaseModel):
    step_number: Any
    title: Any
    description: Any
    estimated_duration: Optional[Any] = None
    resources: Optional[Any] = None


class RoadmapSummary(BaseModel):
    profession: str
    is_regulated: bool
    path_type: Any          # "Regulated" | "Unregulated"
    total_estimated_years: Optional[Any] = None
    steps: Any
    key_links: Optional[Any] = None
    important_notes: Optional[Any] = None





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
