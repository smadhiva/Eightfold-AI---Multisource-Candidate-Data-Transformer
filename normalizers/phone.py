from typing import Optional
import phonenumbers

def normalize_phone(raw: str, default_region: str = "US") -> Optional[str]:
    if not raw:
        return None
    try:
        p = phonenumbers.parse(raw, default_region)
        if phonenumbers.is_possible_number(p):
            return phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)
        return None
    except Exception:
        return None
