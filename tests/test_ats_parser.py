"""Tests for ATS JSON parser"""
from parsers.ats_parser import parse_ats_json
import json
import tempfile
import os


def test_ats_json_parser():
    """ATS parser should handle flexible JSON field names."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1-555-0123",
            "skills": ["Python", "Go"],
            "title": "Senior Engineer"
        }, f)
        fname = f.name
    
    result = parse_ats_json(fname)
    try:
        os.unlink(fname)
    except Exception:
        pass
        
    assert result["source"] == "ats"
    assert result["name"] == "Test User"
    assert "test@example.com" in result["emails"]


def test_ats_json_missing_file():
    """ATS parser should fail gracefully on missing file."""
    result = parse_ats_json("/nonexistent/file.json")
    assert result["source"] == "ats"
    assert result["name"] is None
    assert result["emails"] == []
