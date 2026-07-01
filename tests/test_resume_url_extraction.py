"""Tests for URL extraction from resume"""
from parsers.resume_parser import parse_resume
import tempfile
import os


def test_resume_extracts_linkedin_url():
    """Resume parser should extract LinkedIn URL."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""John Doe
Senior Engineer
john@example.com
+1 555 0123
LinkedIn: https://www.linkedin.com/in/johndoe
GitHub: https://github.com/johndoe

Skills:
Python, SQL
""")
        fname = f.name
    
    result = parse_resume(fname)
    try:
        os.unlink(fname)
    except Exception:
        pass
        
    assert result["source"] == "resume"
    assert result["linkedin_url"] == "https://www.linkedin.com/in/johndoe"
    assert result["github_url"] == "https://github.com/johndoe"


def test_resume_extracts_github_url():
    """Resume parser should extract GitHub URL."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""Jane Smith
Engineer
jane@example.com
GitHub: https://github.com/janesmith

Skills:
Python
""")
        fname = f.name
    
    result = parse_resume(fname)
    try:
        os.unlink(fname)
    except Exception:
        pass
        
    assert result["source"] == "resume"
    assert result["github_url"] == "https://github.com/janesmith"


def test_resume_url_not_found():
    """Resume parser should handle missing URLs gracefully."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""Bob Johnson
Engineer
bob@example.com

Skills:
Python
""")
        fname = f.name
    
    result = parse_resume(fname)
    try:
        os.unlink(fname)
    except Exception:
        pass
        
    assert result["source"] == "resume"
    assert result["linkedin_url"] is None
    assert result["github_url"] is None
    assert result["links"] == []
