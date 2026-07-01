from typing import Optional

def normalize_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    # basic title case and strip extra whitespace
    return " ".join([p.capitalize() for p in name.strip().split()])
