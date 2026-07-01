#!/usr/bin/env bash
set -euo pipefail
python main.py --csv inputs/recruiter.csv --resume inputs/resume.txt --linkedin inputs/linkedin.html --config config/default.json
echo "Demo complete. Output in output/"
