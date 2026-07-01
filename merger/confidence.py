from typing import Dict, List

def compute_confidence(merged: Dict, sources: List[Dict], source_scores: Dict[str, float]) -> Dict:
    """Compute confidence per field and overall confidence.

    `sources` is a list of original profiles (with `source` keys) that contributed.
    """
    field_conf = {}
    # For simple fields, if any source provided it, take max confidence weighted by occurrences
    for field in ["full_name", "headline"]:
        if field == "full_name":
            contributors = [s for s in sources if s.get("full_name") or s.get("name")]
        else:
            contributors = [s for s in sources if s.get("headline")]
            
        if contributors:
            scores = [source_scores.get(s.get("source"), 0.5) for s in contributors]
            field_conf[field] = min(1.0, max(scores))
        else:
            field_conf[field] = 0.0

    # lists: emails/phones/skills - confidence increases with multiple confirmations
    for list_field in ["emails", "phones", "skills"]:
        vals = merged.get(list_field, [])
        cf = {}
        for v in vals:
            contributors = 0
            score_sum = 0.0
            for s in sources:
                if v in (s.get(list_field) or []):
                    contributors += 1
                    score_sum += source_scores.get(s.get("source"), 0.5)
            if contributors == 0:
                cf[v] = 0.0
            else:
                # average score scaled by confirmations, capped at 1.0
                avg = score_sum / contributors
                cf[v] = min(1.0, avg + 0.05 * (contributors - 1))
        field_conf[list_field] = cf

    # overall confidence: average of key field confidences
    primitive_scores = [v for k, v in field_conf.items() if isinstance(v, float)]
    list_scores = []
    for k, v in field_conf.items():
        if isinstance(v, dict) and v:
            list_scores.append(sum(v.values()) / len(v))
    all_scores = primitive_scores + list_scores
    overall = float(sum(all_scores) / len(all_scores)) if all_scores else 0.0

    return {"fields": field_conf, "overall": min(1.0, overall)}
