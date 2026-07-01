from merger.merge import merge_profiles
from merger.confidence import compute_confidence

def test_merge_and_confidence():
    profiles = [
        {"source": "csv", "emails": ["a@x.com"], "name": "A"},
        {"source": "linkedin", "emails": ["a@x.com","b@x.com"], "name": "A B"},
        {"source": "resume", "emails": ["b@x.com"], "name": "A B C"}
    ]
    merged = merge_profiles(profiles)
    conf = compute_confidence(merged, profiles, {"resume": 0.95, "linkedin": 0.9, "csv": 0.8})
    assert "emails" in merged and merged["emails"]
    assert 0.0 <= conf["overall"] <= 1.0
