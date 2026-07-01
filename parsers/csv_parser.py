from typing import Dict, Any
import pandas as pd
import numpy as np

def parse_recruiter_csv(path: str) -> Dict[str, Any]:
    """Parse recruiter CSV into a structured dict. Handles malformed columns gracefully."""
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV {path}: {e}")

    # case-insensitive lookup
    cols = {c.lower(): c for c in df.columns}
    
    def get(name):
        if name not in cols or df.empty:
            return None
        val = df[cols[name]].iloc[0]
        # Handle NaN (float) and "nan" (string)
        if pd.isna(val):
            return None
        val = str(val).strip()
        if val.lower() == "nan" or not val:
            return None
        return val

    result = {
        "source": "csv",
        "name": get("name"),
        "email": get("email") or get("emails"),
        "phone": get("phone") or get("phones"),
        "company": get("company"),
        "job_title": get("job title") or get("title"),
        "location": get("location")
    }

    # normalize into lists where appropriate
    if result["email"]:
        result["emails"] = [s.strip() for s in str(result.pop("email")).split(";") if s.strip()]
    else:
        result.setdefault("emails", [])
        result.pop("email", None)

    if result["phone"]:
        result["phones"] = [s.strip() for s in str(result.pop("phone")).split(";") if s.strip()]
    else:
        result.setdefault("phones", [])
        result.pop("phone", None)

    return result

