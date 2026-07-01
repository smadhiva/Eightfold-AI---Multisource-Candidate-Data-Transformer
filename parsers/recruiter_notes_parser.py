"""Recruiter notes parser for free-form text"""
import re
from typing import Dict, Any, List


EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+")
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{6,}\d")


def parse_recruiter_notes(path: str) -> Dict[str, Any]:
    """Parse recruiter notes text, extracting name, email, phone, skills via regex."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return {"source": "recruiter_notes", "name": None, "emails": [], "phones": [], "skills": []}

    # Extract emails and phones
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)

    # Try to find name (usually first capitalized phrase)
    name = None
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:5]:
        # Look for capitalized words
        words = line.split()
        if any(w[0].isupper() for w in words) and not any(c.isdigit() for c in line[:20]):
            name = line
            break

    # Extract skills (usually after "Skills:" section header on its own line)
    skills = []
    m = re.search(r"(?:\n|^)Skills\s*:\s*(.*?)(?=\n\n|\nExperience|\nEducation|$)", text, re.IGNORECASE | re.DOTALL)
    if m:
        skills_text = m.group(1)
        skills = [s.strip() for s in re.split(r"[,;•\n]", skills_text) if s.strip() and len(s.strip()) < 50]

    return {
        "source": "recruiter_notes",
        "name": name,
        "emails": list(dict.fromkeys(emails)),
        "phones": list(dict.fromkeys(phones)),
        "skills": skills,
        "raw_text": text,
    }
