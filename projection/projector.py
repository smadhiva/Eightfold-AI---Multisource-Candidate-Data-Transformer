from typing import Any, Dict, List
from normalizers.phone import normalize_phone

def _resolve_path(profile: Dict[str, Any], expr: str) -> Any:
    if not expr:
        return None
    try:
        # Check for array mapping like skills[].name
        if "[]" in expr:
            base, rest = expr.split("[]", 1)
            val_list = profile.get(base.strip(), [])
            if not isinstance(val_list, list):
                return None
            
            sub_path = rest.lstrip(".") # e.g. "name"
            if sub_path:
                out = []
                for item in val_list:
                    if isinstance(item, dict):
                        if sub_path in item:
                            out.append(item[sub_path])
                    else:
                        # If list contains strings/primitives, just return them
                        out.append(item)
                return out
            return val_list

        # Check for indexed expression like emails[0]
        if "[" in expr and "]" in expr:
            base, rest = expr.split("[", 1)
            idx_str, rest = rest.split("]", 1)
            idx = int(idx_str)
            val_list = profile.get(base.strip(), [])
            val = val_list[idx] if isinstance(val_list, list) and len(val_list) > idx else None
            if rest.startswith("."):
                sub_path = rest[1:]
                if isinstance(val, dict):
                    return val.get(sub_path)
            return val

        # Simple field access
        return profile.get(expr)
    except Exception:
        return None

def apply_projection(profile: Dict[str, Any], projection_cfg: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    
    # Get general configuration options
    include_confidence = projection_cfg.get("include_confidence", True)
    include_provenance = projection_cfg.get("include_provenance", True)
    on_missing = projection_cfg.get("on_missing", "null") # "null", "omit", "error"

    for f in projection_cfg.get("fields", []):
        path = f.get("path")
        src = f.get("from") or path # fallback to path if 'from' is not specified
        required = f.get("required", False)
        norm_type = f.get("normalize")

        # Resolve value
        val = _resolve_path(profile, src)

        # Apply normalization
        if val is not None:
            if norm_type == "E.164":
                if isinstance(val, list):
                    val = [normalize_phone(v) or v for v in val]
                else:
                    val = normalize_phone(val) or val
            elif norm_type == "canonical":
                # skills are already normalized in the pipeline or synonyms mapping can be applied here
                pass

        # Handle missing values
        if val is None or val == [] or val == "":
            if required:
                raise ValueError(f"Required field '{path}' (from '{src}') is missing.")
            
            if on_missing == "error":
                raise ValueError(f"Field '{path}' is missing and on_missing is set to error.")
            elif on_missing == "omit":
                continue
            else: # "null"
                out[path] = None
        else:
            out[path] = val

    # Include overall confidence and provenance if requested and present
    if include_confidence and "overall_confidence" in profile:
        out["overall_confidence"] = profile["overall_confidence"]
    if include_provenance and "provenance" in profile:
        out["provenance"] = profile["provenance"]

    return out
