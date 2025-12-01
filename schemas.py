from pydantic import BaseModel, Field
from typing import List, Optional

class CandidateProfile(BaseModel):
    name: str
    contact: str
    summary: str
    skills: List[str]
    experience: List[str]
    education: List[str]
    extras: Optional[List[str]] = None

class JobRequirements(BaseModel):
    title: str
    company: str
    must_haves: List[str]
    nice_to_haves: List[str]
    responsibilities: List[str]
    location: Optional[str] = None

class StrategyPlan(BaseModel):
    gaps: List[str]
    positioning: List[str]
    rewriting_focus: List[str]

class DraftContent(BaseModel):
    tailored_resume: str
    tailored_cover: Optional[str]

class ValidationResult(BaseModel):
    passes: bool
    reasons: List[str]
    suggestions: Optional[List[str]] = None
