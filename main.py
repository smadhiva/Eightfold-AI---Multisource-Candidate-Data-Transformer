"""CLI entrypoint for candidate-transformer"""
from typing import Optional
import typer
import json
import os
from parsers.csv_parser import parse_recruiter_csv
from parsers.resume_parser import parse_resume
from parsers.linkedin_parser import parse_linkedin
from parsers.github_parser import parse_github
from parsers.ats_parser import parse_ats_json
from parsers.recruiter_notes_parser import parse_recruiter_notes
from normalizers.names import normalize_name
from normalizers.phone import normalize_phone
from normalizers.skills import load_synonyms, normalize_skills
from normalizers.location import normalize_location
from merger.merge import merge_profiles
from merger.confidence import compute_confidence
from projection.projector import apply_projection
from validator.schema import CandidateModel
from output.exporter import export_json

app = typer.Typer()


@app.command()
def run(
    csv: Optional[str] = None,
    resume: Optional[str] = None,
    linkedin: Optional[str] = None,
    github: Optional[str] = None,
    ats_json: Optional[str] = None,
    recruiter_notes: Optional[str] = None,
    config: str = "config/default.json",
    outdir: str = "output"
):
    os.makedirs(outdir, exist_ok=True)

    profiles = []
    
    # Parse resume first to extract LinkedIn/GitHub URLs if not provided
    resume_data = None
    if resume:
        try:
            resume_data = parse_resume(resume)
            profiles.append(resume_data)
            # Extract URLs from resume if not provided as CLI args
            if not linkedin and resume_data.get("linkedin_url"):
                linkedin = resume_data["linkedin_url"]
                typer.echo(f"Extracted LinkedIn URL from resume: {linkedin}")
            if not github and resume_data.get("github_url"):
                github = resume_data["github_url"]
                typer.echo(f"Extracted GitHub URL from resume: {github}")
        except Exception as e:
            typer.echo(f"Resume parse failed: {e}")
    
    if csv:
        try:
            c = parse_recruiter_csv(csv)
            profiles.append(c)
        except Exception as e:
            typer.echo(f"CSV parse failed: {e}")

    if linkedin:
        try:
            l = parse_linkedin(linkedin)
            profiles.append(l)
        except Exception as e:
            typer.echo(f"LinkedIn parse failed: {e}")

    if github:
        try:
            g = parse_github(github)
            profiles.append(g)
        except Exception as e:
            typer.echo(f"GitHub parse failed: {e}")

    if ats_json:
        try:
            a = parse_ats_json(ats_json)
            profiles.append(a)
        except Exception as e:
            typer.echo(f"ATS JSON parse failed: {e}")

    if recruiter_notes:
        try:
            n = parse_recruiter_notes(recruiter_notes)
            profiles.append(n)
        except Exception as e:
            typer.echo(f"Recruiter notes parse failed: {e}")

    # normalization
    cfg = {}
    try:
        with open(config, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        pass

    synonyms = cfg.get("skills_synonyms", {})
    for p in profiles:
        if p.get("name"):
            p["name"] = normalize_name(p["name"]) or p["name"]
        if p.get("location"):
            p["location"] = normalize_location(p["location"]) or p["location"]
        if p.get("phones"):
            p["phones"] = [normalized for ph in p.get("phones") if (normalized := normalize_phone(ph, cfg.get("default_phone_region", "US")))]
        if p.get("skills"):
            p["skills"] = normalize_skills(p.get("skills"), synonyms)

    merged = merge_profiles(profiles)

    # confidence
    source_scores = cfg.get("source_confidence", {"resume": 0.95, "linkedin": 0.9, "csv": 0.8})
    conf = compute_confidence(merged, profiles, source_scores)
    merged["overall_confidence"] = conf.get("overall", 0.0)
    merged["confidence_fields"] = conf.get("fields")

    # validate
    try:
        candidate = CandidateModel(**merged)
    except Exception as e:
        typer.echo(f"Validation failed: {e}")
        candidate = None

    # export canonical
    canon_path = os.path.join(outdir, "canonical.json")
    export_json(merged, canon_path)

    # projection
    proj_cfg = cfg.get("projection", {})
    projected = apply_projection(merged, proj_cfg)
    proj_path = os.path.join(outdir, "projected.json")
    export_json(projected, proj_path)

    typer.echo(f"Exported canonical -> {canon_path}")
    typer.echo(f"Exported projected -> {proj_path}")


if __name__ == "__main__":
    app()
