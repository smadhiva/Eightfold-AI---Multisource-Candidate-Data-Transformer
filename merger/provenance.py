from typing import Dict

def add_provenance(prov: Dict, field: str, source: str, method: str):
    prov.setdefault(field, [])
    prov[field].append({"field": field, "source": source, "method": method})
