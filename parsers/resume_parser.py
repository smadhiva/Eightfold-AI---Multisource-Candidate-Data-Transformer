import re
from typing import Dict, Any, List
import pdfplumber
import os

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+")
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{6,}\d")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+")
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+")
URL_RE = re.compile(r"https?://[^\s]+")


def _extract_text_from_pdf(path: str) -> str:
    try:
        with pdfplumber.open(path) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
            return "\n".join(pages)
    except Exception:
        return ""


def _extract_section(text: str, section_name: str, max_lines: int = 50) -> str:
    """Extract section content from resume text."""
    pattern = rf"(?:{section_name})\s*(?:\n|:)([\s\S]{{1,{max_lines*50}}}?)(?=\n[A-Z][a-zA-Z\s]*(?:\n|:)|$)"
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m and m.group(1) else ""


def _parse_bullet_list(section_text: str) -> List[str]:
    """Parse bullet points from section text."""
    lines = [l.strip() for l in section_text.split("\n") if l.strip()]
    items = [l for l in lines if l.startswith(("•", "-", "*", "•"))]
    return items

def _clean_str(s: str) -> str:
    if not s:
        return None
    # Remove leading non-alphanumeric/non-bracket/non-quote characters, except spaces after cleaning
    cleaned = re.sub(r"^[^a-zA-Z0-9\(\'\"]+", "", s.strip()).strip()
    return cleaned if cleaned else None

def parse_edu_entry(entry: str) -> Dict[str, Any]:
    edu_data = {"school": None, "degree": None, "field": None, "year": None, "raw": entry}
    years = re.findall(r"\b(19\d{2}|20\d{2})\b", entry)
    if years:
        edu_data["year"] = int(years[-1])
    degree_m = re.search(r"\b(B\.Tech|B\.S\.|M\.S\.|B\.E\.|B\.A\.|M\.Tech|Bachelor|Master|Ph\.D)\b", entry, re.IGNORECASE)
    if degree_m:
        edu_data["degree"] = _clean_str(degree_m.group(1))
    school_m = re.search(r"([^,]+(?:University|Institute|Vidyapeetham|College|School|Academy)[^,(]*)", entry, re.IGNORECASE)
    if school_m:
        edu_data["school"] = _clean_str(school_m.group(1))
    else:
        parts = entry.split(",")
        if len(parts) > 1:
            edu_data["school"] = _clean_str(parts[1])
    field_m = re.search(r"(?:in|of)\s+([^,(]+)", entry, re.IGNORECASE)
    if field_m:
        field_candidate = field_m.group(1).strip()
        if not any(w in field_candidate.lower() for w in ["university", "institute", "vidyapeetham", "college"]):
            edu_data["field"] = _clean_str(field_candidate)
    return edu_data

def parse_exp_entry(entry: str) -> Dict[str, Any]:
    exp_data = {"company": None, "title": None, "start": None, "end": None, "description": "", "raw": entry}
    date_range_m = re.search(r"\b([A-Za-z]{3,9}\s+\d{4}|\d{4})\s*[-–—]\s*([A-Za-z]{3,9}\s+\d{4}|\d{4}|Present)\b", entry, re.IGNORECASE)
    if date_range_m:
        exp_data["start"] = date_range_m.group(1).strip()
        exp_data["end"] = date_range_m.group(2).strip()
    
    clean_text = entry
    if date_range_m:
        clean_text = entry[:date_range_m.start()].strip()
    parts = re.split(r"[,–—]", clean_text)
    if len(parts) >= 2:
        exp_data["title"] = _clean_str(parts[0])
        exp_data["company"] = _clean_str(parts[1])
    elif len(parts) == 1:
        exp_data["title"] = _clean_str(parts[0])
        
    lines = [l.strip() for l in entry.split("\n") if l.strip()]
    if len(lines) > 1:
        exp_data["description"] = " ".join([_clean_str(l) for l in lines[1:] if _clean_str(l)])
    return exp_data

def parse_project_entry(entry: str) -> Dict[str, Any]:
    proj_data = {"title": None, "description": "", "url": None, "raw": entry}
    lines = [l.strip() for l in entry.split("\n") if l.strip()]
    if not lines:
        return proj_data
    first_line = lines[0]
    title_part = re.split(r"[:–—]", first_line)[0].strip()
    proj_data["title"] = _clean_str(title_part)
    
    desc_parts = []
    if len(lines) > 1:
        desc_parts.extend([_clean_str(l) for l in lines[1:] if _clean_str(l)])
    else:
        dash_split = re.split(r"[:–—]", first_line, maxsplit=1)
        if len(dash_split) > 1:
            desc_parts.append(_clean_str(dash_split[1]))
    proj_data["description"] = " ".join(desc_parts)
    
    urls = re.findall(r"https?://[^\s]+", entry)
    if urls:
        proj_data["url"] = urls[0]
    return proj_data


def parse_resume(path: str) -> Dict[str, Any]:
    """Parse resume (PDF preferred, TXT fallback) and extract structured fields."""
    text = ""
    if path.lower().endswith(".pdf"):
        text = _extract_text_from_pdf(path)

    if not text and os.path.exists(path):
        # fallback to plain text
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            text = ""

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    
    # Extract URLs
    linkedin_urls = LINKEDIN_RE.findall(text)
    github_urls = GITHUB_RE.findall(text)
    all_urls = URL_RE.findall(text)

    name = None
    headline = None
    summary = None
    if lines:
        name = lines[0]
        if len(lines) > 1:
            candidate = lines[1]
            if not any(w in candidate.lower() for w in ["@", "phone", "github", "linkedin", "http", "+91", "|"]):
                headline = candidate

    # Extract summary
    summary_section = _extract_section(text, "Summary")
    if summary_section:
        summary = summary_section.split("\n")[0][:200]
        
    if not headline and summary:
        headline = summary

    # Extract skills
    skills = []
    skills_section = _extract_section(text, "Skills|Technical Skills")
    if skills_section:
        words = re.findall(r"[\w\+\#\-\.]+", skills_section)
        exclude_words = {"languages", "frameworks", "libraries", "developer", "tools", "skills", "and", "the", "with"}
        skills = [w for w in words if len(w) > 2 and w.lower() not in exclude_words][:30]

    # Extract education
    education = []
    edu_section = _extract_section(text, "Education")
    if edu_section:
        entries = re.split(r"\n(?=•|-|\*|[A-Z][A-Za-z])", edu_section)
        for entry in entries[:5]:
            if entry.strip():
                education.append(parse_edu_entry(entry.strip()))

    # Extract experience
    experience = []
    exp_section = _extract_section(text, "Experience|Work Experience")
    if exp_section:
        entries = re.split(r"\n(?=•|-|\*|[A-Z][A-Za-z])", exp_section)
        for entry in entries[:5]:
            if entry.strip() and len(entry.strip()) > 20:
                experience.append(parse_exp_entry(entry.strip()))

    # Extract projects
    projects = []
    proj_section = _extract_section(text, "Projects|Portfolio")
    if proj_section:
        entries = re.split(r"\n(?=•|-|\*|[A-Z][A-Za-z])", proj_section)
        for entry in entries[:5]:
            if entry.strip() and len(entry.strip()) > 20:
                projects.append(parse_project_entry(entry.strip()))

    # Extract certifications
    certifications = []
    cert_section = _extract_section(text, "Certifications|Certificates")
    if cert_section:
        lines_cert = [l.strip() for l in cert_section.split("\n") if l.strip()]
        certifications = lines_cert[:10]

    return {
        "source": "resume",
        "name": name,
        "headline": headline,
        "summary": summary,
        "emails": list(dict.fromkeys(emails)),
        "phones": list(dict.fromkeys(phones)),
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "certifications": certifications,
        "linkedin_url": linkedin_urls[0] if linkedin_urls else None,
        "github_url": github_urls[0] if github_urls else None,
        "links": list(dict.fromkeys(linkedin_urls + github_urls + all_urls)),
        "raw_text": text
    }
