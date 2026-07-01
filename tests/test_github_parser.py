"""Tests for GitHub parser"""
from parsers.github_parser import parse_github


def test_github_parser_returns_dict():
    """GitHub parser should return dict even if offline or invalid."""
    result = parse_github("torvalds")  # Linus Torvalds' public GitHub
    assert result["source"] == "github"
    # May or may not fetch live, but should not crash
    assert isinstance(result, dict)


def test_github_parser_url_format():
    """GitHub parser should handle both URL and username."""
    result1 = parse_github("torvalds")
    result2 = parse_github("https://github.com/torvalds")
    assert result1["source"] == "github"
    assert result2["source"] == "github"
