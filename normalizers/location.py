from typing import Optional

def normalize_location(loc: Optional[str]) -> Optional[str]:
    if not loc:
        return None
    return ", ".join([p.strip().title() for p in loc.split(",")])
