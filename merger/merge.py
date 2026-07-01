from typing import List, Dict, Any
from .provenance import add_provenance

def _unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for it in items:
        if it and it not in seen:
            out.append(it)
            seen.add(it)
    return out

def merge_profiles(profiles: List[Dict[str, Any]], priorities: List[str] = ["resume", "linkedin", "csv"]) -> Dict[str, Any]:
    """Merge multiple profile dicts into a canonical partial profile. Collect provenance."""
    merged: Dict[str, Any] = {
        "name": None, "full_name": None, "headline": None, "emails": [], "phones": [], "skills": [],
        "experience": [], "education": [], "links": [], "certifications": [], "projects": [],
        "linkedin_url": None, "github_url": None
    }
    provenance = {}

    # sort profiles by priority
    order = {p: i for i, p in enumerate(priorities)}
    profiles_sorted = sorted(profiles, key=lambda p: order.get(p.get("source"), 999))

    experience_map = {}
    education_map = {}
    projects_map = {}

    for p in profiles_sorted:
        src = p.get("source")

        # name & headline: prefer first non-empty by priority
        if p.get("name") and not merged.get("full_name"):
            merged["full_name"] = p.get("name")
            merged["name"] = p.get("name")
            add_provenance(provenance, "full_name", src, "direct")
            add_provenance(provenance, "name", src, "direct")

        if p.get("headline") and not merged.get("headline"):
            merged["headline"] = p.get("headline")
            add_provenance(provenance, "headline", src, "direct")

        # linkedin & github urls
        if p.get("linkedin_url") and not merged.get("linkedin_url"):
            merged["linkedin_url"] = p.get("linkedin_url")
            add_provenance(provenance, "linkedin_url", src, "direct")
            
        if p.get("github_url") and not merged.get("github_url"):
            merged["github_url"] = p.get("github_url")
            add_provenance(provenance, "github_url", src, "direct")

        # collect lists
        if p.get("emails"):
            merged["emails"].extend(p.get("emails", []))
            add_provenance(provenance, "emails", src, "direct")
        if p.get("phones"):
            merged["phones"].extend(p.get("phones", []))
            add_provenance(provenance, "phones", src, "direct")
        if p.get("skills"):
            merged["skills"].extend(p.get("skills", []))
            add_provenance(provenance, "skills", src, "direct")
        if p.get("links"):
            merged["links"].extend(p.get("links", []) or [])
            add_provenance(provenance, "links", src, "direct")
        if p.get("certifications"):
            merged["certifications"].extend(p.get("certifications", []))
            add_provenance(provenance, "certifications", src, "direct")

        # experience merging: deduplicate and update dates/descriptions
        for exp in p.get("experience", []):
            comp = (exp.get("company") or "").strip()
            title = (exp.get("title") or "").strip()
            if not comp and not title:
                continue
                
            # Smart matching by company name similarity & title keywords
            matched_key = None
            comp_clean = comp.lower().replace("systems", "").replace("inc", "").replace("corp", "").replace("co.", "").strip()
            for key in list(experience_map.keys()):
                existing_comp, existing_title = key
                existing_comp_clean = existing_comp.lower().replace("systems", "").replace("inc", "").replace("corp", "").replace("co.", "").strip()
                
                # If companies match or are substrings
                if comp_clean in existing_comp_clean or existing_comp_clean in comp_clean:
                    title_words = set(title.lower().split())
                    existing_title_words = set(existing_title.lower().split())
                    # If they share at least one keyword (e.g. Intern) or one title is a subset, or one is missing
                    if title_words.intersection(existing_title_words) or not title or not existing_title:
                        matched_key = key
                        break
            
            key = (comp.lower(), title.lower())
            if not matched_key:
                experience_map[key] = exp.copy()
                add_provenance(provenance, "experience", src, "direct")
            else:
                existing = experience_map[matched_key]
                add_provenance(provenance, "experience", src, "merge_update")
                # Prefer LinkedIn dates and detailed titles
                if src == "linkedin":
                    if exp.get("start"):
                        existing["start"] = exp["start"]
                    if exp.get("end"):
                        existing["end"] = exp["end"]
                    if exp.get("description"):
                        existing["description"] = exp["description"]
                    if exp.get("title"):
                        existing["title"] = exp["title"]
                else:
                    if exp.get("start") and not existing.get("start"):
                        existing["start"] = exp["start"]
                    if exp.get("end") and not existing.get("end"):
                        existing["end"] = exp["end"]
                    if exp.get("description") and not existing.get("description"):
                        existing["description"] = exp["description"]

        # education merging: deduplicate and update fields
        for edu in p.get("education", []):
            school = (edu.get("school") or edu.get("institution") or "").strip()
            degree = (edu.get("degree") or "").strip()
            if not school and not degree:
                continue
            key = (school.lower(), degree.lower())
            if key not in education_map:
                education_map[key] = edu.copy()
                add_provenance(provenance, "education", src, "direct")
            else:
                existing = education_map[key]
                add_provenance(provenance, "education", src, "merge_update")
                if edu.get("start"):
                    existing["start"] = edu["start"]
                if edu.get("end") or edu.get("end_year"):
                    existing["end"] = edu.get("end") or edu.get("end_year")
                if edu.get("field"):
                    existing["field"] = edu["field"]
                if edu.get("year"):
                    existing["year"] = edu["year"]

        # projects merging: deduplicate by title
        for proj in p.get("projects", []):
            proj_title = (proj.get("title") or "").strip()
            if not proj_title:
                continue
            
            # Smart matching (ignore casing, dashes, or spaces)
            proj_clean = proj_title.lower().replace("-", "").replace(" ", "").replace("_", "")
            matched_key = None
            for key in list(projects_map.keys()):
                if proj_clean in key or key in proj_clean:
                    matched_key = key
                    break
                    
            if not matched_key:
                projects_map[proj_clean] = proj.copy()
                add_provenance(provenance, "projects", src, "direct")
            else:
                existing = projects_map[matched_key]
                add_provenance(provenance, "projects", src, "merge_update")
                if proj.get("url") or proj.get("link"):
                    existing["url"] = proj.get("url") or proj.get("link")
                # Keep longer description
                if proj.get("description") and len(proj.get("description", "")) > len(existing.get("description", "")):
                    existing["description"] = proj["description"]

    merged["experience"] = list(experience_map.values())
    merged["education"] = list(education_map.values())
    merged["projects"] = list(projects_map.values())

    # dedupe
    merged["emails"] = _unique_preserve_order(merged["emails"])[:10]
    merged["phones"] = _unique_preserve_order(merged["phones"])[:10]
    merged["skills"] = _unique_preserve_order(merged["skills"])[:200]
    merged["certifications"] = _unique_preserve_order(merged["certifications"])[:100]

    merged["provenance"] = provenance
    return merged
