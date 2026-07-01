from normalizers.names import normalize_name
from normalizers.skills import normalize_skills, load_synonyms

def test_normalize_name():
    assert normalize_name("john smith") == "John Smith"

def test_normalize_skills(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text('{"skills_synonyms": {"python3": "Python"}}')
    synonyms = load_synonyms(str(cfg))
    out = normalize_skills(["Python3", "SQL"], synonyms)
    assert "Python" in out
