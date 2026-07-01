from typing import Optional
import re

MONTHS = {"jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06", "jul": "07", "aug": "08", "sep": "09", "sept": "09", "oct": "10", "nov": "11", "dec": "12"}

def normalize_month_year(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = text.strip()
    m = re.search(r"([A-Za-z]{3,})\s*(\d{4})", text)
    if m:
        mon = m.group(1)[:3].lower()
        yy = m.group(2)
        mm = MONTHS.get(mon)
        if mm:
            return f"{yy}-{mm}"
    # year only
    m2 = re.search(r"(\d{4})", text)
    if m2:
        return f"{m2.group(1)}"
    return None
