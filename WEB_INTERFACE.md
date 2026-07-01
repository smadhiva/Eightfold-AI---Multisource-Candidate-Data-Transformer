# Web Interface Quick Start Guide

## Starting the Web Server

### Windows

```powershell
# Using PowerShell script
.\run_web.ps1

# Or using streamlit directly
streamlit run web_interface.py
```

### macOS / Linux

```bash
# Using bash script
./run_web.sh

# Or using streamlit directly
streamlit run web_interface.py
```

The interface will open at **http://localhost:8501**

## Using the Web Interface

### Tab 1: 📤 Upload & Extract

1. **Click "Browse files" button**
   - Select a resume PDF or TXT file from your computer

2. **Automatic Extraction**
   - Name, email, phone extracted
   - LinkedIn URL detected (if present)
   - GitHub URL detected (if present)
   - Skills parsed from resume

3. **Optional: Fetch Live Profiles**
   - Click "Fetch LinkedIn Profile" to get public profile data
   - Click "Fetch GitHub Profile" to get repo/language data
   - These are added to the profile automatically

### Tab 2: ✏️ Review & Edit

1. **Review Extracted Data**
   - All fields from resume are shown
   - Fields are editable

2. **Update Fields**
   - Edit name, headline, location
   - Add more emails or phones
   - Update or add LinkedIn/GitHub URLs
   - Add/remove skills

3. **View Experience & Education**
   - Expandable sections for each job and school
   - Edit start dates, end dates, titles, companies

### Tab 3: 📊 Output & Export

1. **View Generated Profile**
   - Canonical profile with all merged data
   - Confidence score (0-100%) for overall profile
   - Projected output (reshaped per config)

2. **Download Results**
   - Download canonical.json (all data + provenance)
   - Download projected.json (configured output)
   - View data lineage (provenance)

3. **Check Confidence Scores**
   - See where each field came from
   - See extraction method
   - Understand how confident the system is

## Example Workflow

```
1. Navigate to http://localhost:8501
2. Upload your resume (resume.pdf or resume.txt)
3. System extracts:
   - Jane Smith
   - jane.smith@company.com
   - +1-415-987-6543
   - https://linkedin.com/in/janesmith
   - https://github.com/janesmith
4. Click "Fetch LinkedIn Profile" button
5. Click "Fetch GitHub Profile" button
6. Go to "Review & Edit" tab and verify data
7. Go to "Output & Export" tab
8. Download canonical_profile.json and projected_profile.json
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"

Install missing dependencies:
```bash
pip install -r requirements.txt
```

### App fails to start

Check Python version:
```python
python --version  # Should be 3.11 or higher
```

Check if port 8501 is in use:
```bash
# Try a different port
streamlit run web_interface.py --server.port 8502
```

### Resume parsing fails

Ensure file is:
- Valid PDF or plain text file
- Not password protected (for PDFs)
- UTF-8 encoded (for TXT)

### GitHub/LinkedIn fetch returns empty data

This happens when:
- Profile is private or doesn't exist
- Network connectivity issue
- Rate limited by API

System gracefully handles this and continues.

## Environment Variables

```bash
# Change port (default 8501)
STREAMLIT_SERVER_PORT=8502 streamlit run web_interface.py

# Set Streamlit logger level
STREAMLIT_LOGGER_LEVEL=debug streamlit run web_interface.py

# Disable auto-rerun on file changes
streamlit run web_interface.py --logger.level=info --client.toolbarMode=minimal
```

## Tips & Tricks

### Resume Format

Best results with:
- **PDF**: Modern PDFs with text layer (not scanned images)
- **TXT**: Plain text with clear sections

### Profile URLs

The system looks for:
- `linkedin.com/in/username`
- `github.com/username`
- Full URLs: `https://www.linkedin.com/in/username`

### Skills Extraction

Resume should have a "Skills" section:
```
Skills:
Python, JavaScript, Go, Kubernetes, Docker
```

Or:
```
Skills
- Python
- JavaScript
- Go
- Kubernetes
```

### Confidence Scores

- **0.95**: Resume (highest trust)
- **0.90**: LinkedIn
- **0.85**: GitHub
- **0.80**: ATS JSON
- **0.75**: CSV
- **0.70**: Recruiter notes

Multi-source confirmation boosts confidence.

## Support

For issues or feature requests, see the main README.md or create an issue.
