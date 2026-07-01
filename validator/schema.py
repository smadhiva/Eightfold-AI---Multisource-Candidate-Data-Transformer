from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Any
from uuid import uuid4


class Experience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None


class Education(BaseModel):
    school: Optional[str] = Field(None, alias="institution")
    degree: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = Field(None, alias="end_year")
    field: Optional[str] = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class CandidateModel(BaseModel):
    candidate_id: str = Field(default_factory=lambda: str(uuid4()))
    full_name: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    headline: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[dict] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    overall_confidence: float = 0.0
    provenance: dict = Field(default_factory=dict)

    @field_validator("overall_confidence")
    @classmethod
    def check_confidence(cls, v):
        if v < 0 or v > 1:
            raise ValueError("overall_confidence must be between 0 and 1")
        return v

    @field_validator("emails", mode="before")
    @classmethod
    def clean_emails(cls, v):
        """Filter out invalid email-like strings."""
        if not isinstance(v, list):
            return v or []
        # Simple email validation: must contain @
        return [e for e in v if isinstance(e, str) and "@" in e]

    model_config = ConfigDict(extra="allow")
