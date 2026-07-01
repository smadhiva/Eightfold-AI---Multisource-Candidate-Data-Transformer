from typing import List, Optional
import json
import os

def load_synonyms(config_path: str = None) -> dict:
    if not config_path:
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            return cfg.get("skills_synonyms", {})
    except Exception:
        return {}

def normalize_skill(s: str, synonyms: dict) -> str:
    if not s:
        return s
    key = s.strip().lower().replace(" ", "")
    return synonyms.get(key, s.strip())

def normalize_skills(skills: List[str], synonyms: dict) -> List[str]:
    out = []
    for s in skills or []:
        normalized = normalize_skill(s, synonyms)
        if normalized and normalized not in out:
            out.append(normalized)
    return out
