from parsers.csv_parser import parse_recruiter_csv
import os

def test_csv_parser():
    path = os.path.join("inputs", "recruiter.csv")
    res = parse_recruiter_csv(path)
    assert res["source"] == "csv"
    assert "emails" in res and res["emails"]
