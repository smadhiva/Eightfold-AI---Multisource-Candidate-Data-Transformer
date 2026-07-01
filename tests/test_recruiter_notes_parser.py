"""Tests for recruiter notes parser"""
from parsers.recruiter_notes_parser import parse_recruiter_notes
import tempfile
import os


def test_recruiter_notes_parser():
    """Recruiter notes parser should extract name, email, phone, skills."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""John Doe
Senior Engineer
john@example.com
+1 555 0123

Skills:
Python, SQL, React, Kubernetes

Experience:
- Senior Engineer at TechCorp
""")
        fname = f.name
    
    result = parse_recruiter_notes(fname)
    try:
        os.unlink(fname)
    except Exception:
        pass
        
    assert result["source"] == "recruiter_notes"
    assert result["name"] is not None
    assert "john@example.com" in result["emails"]
    assert len(result["skills"]) > 0


def test_recruiter_notes_missing_file():
    """Recruiter notes parser should fail gracefully on missing file."""
    result = parse_recruiter_notes("/nonexistent/notes.txt")
    assert result["source"] == "recruiter_notes"
    assert result["emails"] == []
