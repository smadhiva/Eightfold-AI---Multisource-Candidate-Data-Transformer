"""Edge case tests for robustness"""
from parsers.csv_parser import parse_recruiter_csv
from parsers.resume_parser import parse_resume
from merger.merge import merge_profiles


def test_missing_resume():
    """Parser should handle missing resume gracefully."""
    result = parse_resume("/nonexistent/resume.pdf")
    assert result["source"] == "resume"
    assert result["name"] is None
    assert result["emails"] == []


def test_empty_profiles_merge():
    """Merger should handle empty profiles."""
    profiles = []
    merged = merge_profiles(profiles)
    assert merged["emails"] == []
    assert merged["skills"] == []


def test_duplicate_email_deduplication():
    """Merger should deduplicate emails across sources."""
    profiles = [
        {"source": "csv", "emails": ["a@x.com"], "name": "A"},
        {"source": "resume", "emails": ["a@x.com", "b@x.com"], "name": "A"},
    ]
    merged = merge_profiles(profiles)
    # Should have both emails but deduplicated
    assert len(merged["emails"]) == 2
    assert "a@x.com" in merged["emails"]


def test_missing_name_field():
    """Pipeline should handle missing names gracefully."""
    profiles = [
        {"source": "csv", "emails": ["test@x.com"], "name": None}
    ]
    merged = merge_profiles(profiles)
    assert merged.get("full_name") is None
    assert merged["emails"] == ["test@x.com"]


def test_malformed_csv():
    """CSV parser should fail gracefully on malformed data."""
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("Name,Email,Phone\nJohn,,+1234567890")
        fname = f.name
    
    result = parse_recruiter_csv(fname)
    try:
        os.unlink(fname)
    except Exception:
        pass
    
    assert result["source"] == "csv"
    assert result["name"] == "John"
    assert result["emails"] == []
