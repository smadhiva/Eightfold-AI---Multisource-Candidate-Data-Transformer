import pytest
from projection.projector import apply_projection

def test_projector_basic():
    profile = {
        "full_name": "Jane Doe",
        "emails": ["jane@example.com", "doe@example.com"],
        "phones": ["5551234567"],
        "skills": ["Python", "SQL"],
        "overall_confidence": 0.85,
        "provenance": {"full_name": [{"source": "resume"}]}
    }
    
    cfg = {
        "fields": [
            {"path": "name", "from": "full_name"},
            {"path": "email", "from": "emails[0]"},
            {"path": "all_skills", "from": "skills"}
        ],
        "include_confidence": False,
        "include_provenance": False
    }
    
    projected = apply_projection(profile, cfg)
    assert projected == {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "all_skills": ["Python", "SQL"]
    }

def test_projector_normalization_and_provenance():
    profile = {
        "full_name": "Jane Doe",
        "phones": ["+1 555-123-4567"],
        "overall_confidence": 0.85,
        "provenance": {"full_name": [{"source": "resume"}]}
    }
    
    cfg = {
        "fields": [
            {"path": "phone_num", "from": "phones[0]", "normalize": "E.164"}
        ],
        "include_confidence": True,
        "include_provenance": True
    }
    
    projected = apply_projection(profile, cfg)
    assert projected["phone_num"] == "+15551234567"
    assert projected["overall_confidence"] == 0.85
    assert projected["provenance"] == {"full_name": [{"source": "resume"}]}

def test_projector_missing_null():
    profile = {
        "full_name": "Jane Doe"
    }
    
    cfg = {
        "fields": [
            {"path": "name", "from": "full_name"},
            {"path": "missing_field", "from": "nonexistent"}
        ],
        "on_missing": "null"
    }
    
    projected = apply_projection(profile, cfg)
    assert "missing_field" in projected
    assert projected["missing_field"] is None

def test_projector_missing_omit():
    profile = {
        "full_name": "Jane Doe"
    }
    
    cfg = {
        "fields": [
            {"path": "name", "from": "full_name"},
            {"path": "missing_field", "from": "nonexistent"}
        ],
        "on_missing": "omit"
    }
    
    projected = apply_projection(profile, cfg)
    assert "missing_field" not in projected
    assert projected["name"] == "Jane Doe"

def test_projector_missing_error():
    profile = {
        "full_name": "Jane Doe"
    }
    
    cfg = {
        "fields": [
            {"path": "name", "from": "full_name"},
            {"path": "missing_field", "from": "nonexistent"}
        ],
        "on_missing": "error"
    }
    
    with pytest.raises(ValueError):
        apply_projection(profile, cfg)

def test_projector_required_field_error():
    profile = {
        "full_name": "Jane Doe"
    }
    
    cfg = {
        "fields": [
            {"path": "name", "from": "full_name"},
            {"path": "missing_field", "from": "nonexistent", "required": True}
        ],
        "on_missing": "null"
    }
    
    with pytest.raises(ValueError, match="Required field 'missing_field'"):
        apply_projection(profile, cfg)

def test_projector_skills_nested_mapping():
    profile = {
        "skills": [
            {"name": "Python", "confidence": 0.9},
            {"name": "SQL", "confidence": 0.8}
        ]
    }
    
    cfg = {
        "fields": [
            {"path": "skill_names", "from": "skills[].name"}
        ]
    }
    
    projected = apply_projection(profile, cfg)
    assert projected["skill_names"] == ["Python", "SQL"]
