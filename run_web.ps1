# Run the Streamlit web interface on Windows
# Usage: .\run_web.ps1

$pythonExe = ".\.venv\Scripts\python.exe"
$streamlitExe = ".\.venv\Scripts\streamlit.exe"

Write-Host "Starting Candidate Transformer Web Interface..." -ForegroundColor Green
Write-Host "Opening browser at http://localhost:8501" -ForegroundColor Cyan

& $streamlitExe run web_interface.py --logger.level=info
