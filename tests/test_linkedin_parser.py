from parsers.linkedin_parser import parse_linkedin
import os

def test_linkedin_html():
    path = os.path.join("inputs", "linkedin.html")
    res = parse_linkedin(path)
    assert res["source"] == "linkedin"
    assert res["name"] == "John Doe"
    assert "Python" in res["headline"] or res["headline"]
