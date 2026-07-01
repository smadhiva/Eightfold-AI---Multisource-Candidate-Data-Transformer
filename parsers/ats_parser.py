"""ATS JSON parser for semi-structured candidate data"""
import json
from typing import Dict, Any


def parse_ats_json(path: str) -> Dict[str, Any]:
    """Parse ATS JSON blob with flexible field mapping. Fails gracefully."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception:
        return {"source": "ats", "name": None, "emails": [], "phones": [], "skills": []}

    # Map common ATS field names to canonical
    candidate_name = (
        obj.get("name")
        or obj.get("fullName")
        or obj.get("full_name")
        or obj.get("firstName", "") + " " + obj.get("lastName", "")
    ).strip() or None

    emails = []
    if obj.get("email"):
        emails.append(obj["email"])
    if obj.get("emails"):
        emails.extend(obj["emails"] if isinstance(obj["emails"], list) else [obj["emails"]])

    phones = []
    if obj.get("phone"):
        phones.append(obj["phone"])
    if obj.get("phones"):
        phones.extend(obj["phones"] if isinstance(obj["phones"], list) else [obj["phones"]])

    skills = obj.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",")]

    experience = obj.get("experience", [])
    if isinstance(experience, dict):
        experience = [experience]

    education = obj.get("education", [])
    if isinstance(education, dict):
        education = [education]

    return {
        "source": "ats",
        "name": candidate_name,
        "headline": obj.get("title") or obj.get("headline"),
        "emails": list(dict.fromkeys(emails)),
        "phones": list(dict.fromkeys(phones)),
        "skills": skills,
        "location": obj.get("location") or obj.get("address"),
        "experience": experience,
        "education": education,
    }
