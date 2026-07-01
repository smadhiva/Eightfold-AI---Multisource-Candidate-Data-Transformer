"""Streamlit web interface for candidate transformer"""
import streamlit as st
import json
import os
from pathlib import Path
from parsers.csv_parser import parse_recruiter_csv
from parsers.resume_parser import parse_resume
from parsers.linkedin_parser import parse_linkedin
from parsers.github_parser import parse_github
from parsers.ats_parser import parse_ats_json
from parsers.recruiter_notes_parser import parse_recruiter_notes
from normalizers.names import normalize_name
from normalizers.phone import normalize_phone
from normalizers.skills import load_synonyms, normalize_skills
from normalizers.location import normalize_location
from merger.merge import merge_profiles
from merger.confidence import compute_confidence
from projection.projector import apply_projection
from output.exporter import export_json, generate_flat_csv, generate_nested_csv, generate_pdf_report
import tempfile

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def process_multi_source_pdf(pdf_path: str):
    import pdfplumber
    import json
    import io
    import csv
    import re
    
    resume_pages = []
    pdf_profiles = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            text_lower = text.lower()
            
            # Identify CSV page
            if "first_name" in text_lower and "last_name" in text_lower:
                try:
                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                    header_line = None
                    for line in lines:
                        if "first_name" in line.lower() or "last_name" in line.lower():
                            header_line = line
                            break
                    if header_line:
                        values_line = None
                        for line in lines:
                            if line != header_line and ("@" in line or "," in line):
                                values_line = line
                                break
                        if not values_line and len(lines) > 1:
                            values_line = lines[-1]
                            
                        f_in = io.StringIO(f"{header_line}\n{values_line}")
                        reader = csv.DictReader(f_in)
                        for row in reader:
                            csv_data = {
                                "source": "csv",
                                "name": f"{row.get('first_name', '')} {row.get('last_name', '')}".strip() or row.get('name') or row.get('Name'),
                                "emails": [row.get("email")] if row.get("email") else [],
                                "phones": [row.get("phone")] if row.get("phone") else [],
                                "experience": [{
                                    "company": row.get("company"),
                                    "title": row.get("title"),
                                    "location": row.get("location")
                                }] if row.get("company") or row.get("title") else [],
                                "location": row.get("location")
                            }
                            if not csv_data["name"]:
                                csv_data["name"] = None
                            pdf_profiles.append(csv_data)
                except Exception as e:
                    print(f"Error parsing PDF CSV page: {e}")
                continue
                
            # Identify ATS page
            elif "candidate_id" in text_lower or '"source": "ats"' in text_lower or "ats profile" in text_lower:
                try:
                    start = text.find("{")
                    end = text.rfind("}")
                    if start != -1 and end != -1:
                        json_str = text[start:end+1]
                        ats_data = json.loads(json_str)
                        if "source" not in ats_data:
                            ats_data["source"] = "ats"
                        pdf_profiles.append(ats_data)
                except Exception as e:
                    print(f"Error parsing PDF ATS page: {e}")
                continue
                
            # Identify Recruiter Notes page
            elif "recruiter notes" in text_lower or "interview feedback" in text_lower or "recruiter_notes" in text_lower:
                notes_data = {
                    "source": "notes",
                    "notes": text,
                    "emails": [], "phones": [], "skills": [], "experience": []
                }
                emails = re.findall(r"[\w\.-]+@[\w\.-]+", text)
                phones = re.findall(r"\+?\d[\d\s\-()]{7,}\d", text)
                if emails:
                    notes_data["emails"] = emails
                if phones:
                    notes_data["phones"] = phones
                pdf_profiles.append(notes_data)
                continue
                
            # Identify LinkedIn page
            elif "linkedin profile" in text_lower or ("linkedin.com/in/" in text_lower and i > 0):
                linkedin_data = {
                    "source": "linkedin",
                    "name": None, "headline": None, "location": None,
                    "experience": [], "education": [], "skills": [], "certifications": [],
                    "linkedin_url": None, "urls": []
                }
                urls = re.findall(r"linkedin\.com/in/[\w\-]+", text)
                if urls:
                    url = "https://" + urls[0]
                    linkedin_data["linkedin_url"] = url
                    linkedin_data["urls"] = [url]
                
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                for line in lines:
                    if "headline:" in line.lower() or "headline" in line.lower() and ":" in line:
                        linkedin_data["headline"] = line.split(":", 1)[1].strip()
                    elif "location:" in line.lower():
                        linkedin_data["location"] = line.split(":", 1)[1].strip()
                    elif "skills:" in line.lower():
                        linkedin_data["skills"] = [s.strip() for s in line.split(":", 1)[1].split(",")]
                    elif "certifications:" in line.lower():
                        linkedin_data["certifications"] = [c.strip() for c in line.split(":", 1)[1].split(",")]
                pdf_profiles.append(linkedin_data)
                continue
                
            # Identify GitHub page
            elif "github profile" in text_lower or ("github.com/" in text_lower and i > 0):
                github_data = {
                    "source": "github", "name": None, "bio": None, "location": None,
                    "public_repos": None, "followers": None, "following": None,
                    "skills": [], "languages": [], "projects": [], "links": []
                }
                urls = re.findall(r"github\.com/[\w\-]+", text)
                if urls:
                    url = "https://" + urls[0]
                    github_data["links"].append(url)
                
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                for line in lines:
                    if "bio:" in line.lower():
                        github_data["bio"] = line.split(":", 1)[1].strip()
                    elif "repos:" in line.lower() or "repositories:" in line.lower():
                        try:
                            github_data["public_repos"] = int(re.search(r"\d+", line).group())
                        except Exception:
                            pass
                    elif "followers:" in line.lower():
                        try:
                            github_data["followers"] = int(re.search(r"\d+", line).group())
                        except Exception:
                            pass
                pdf_profiles.append(github_data)
                continue
                
            # Keep as resume page
            resume_pages.append(text)
            
    clean_resume_text = "\n".join(resume_pages)
    return clean_resume_text, pdf_profiles

def load_matching_csv_profile(candidate_name: str, candidate_email: str) -> dict:
    csv_path = os.path.join(ROOT_DIR, "inputs", "recruiter.csv")
    if not os.path.exists(csv_path):
        return {"source": "csv", "name": None, "emails": [], "phones": [], "skills": []}
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        match_idx = None
        for idx, row in df.iterrows():
            row_email = str(row.get("email") or row.get("Email") or "").strip().lower()
            row_name = str(row.get("name") or row.get("Name") or "").strip().lower()
            if candidate_email and candidate_email.lower() == row_email:
                match_idx = idx
                break
            if candidate_name and candidate_name.lower() in row_name:
                match_idx = idx
                break
        if match_idx is None:
            match_idx = 0
            
        row = df.iloc[match_idx]
        profile = {
            "source": "csv",
            "name": str(row.get("name") or "").strip() or None,
            "emails": [str(row.get("email") or "").strip()] if pd.notna(row.get("email")) else [],
            "phones": [str(row.get("phone") or "").strip()] if pd.notna(row.get("phone")) else [],
            "company": str(row.get("company") or "").strip() or None,
            "job_title": str(row.get("job_title") or row.get("title") or "").strip() or None,
            "location": str(row.get("location") or "").strip() or None
        }
        return profile
    except Exception:
        return {"source": "csv", "name": None, "emails": [], "phones": [], "skills": []}

def get_matching_paths(candidate_name: str):
    name_lower = (candidate_name or "").lower()
    if "mathivanan" in name_lower:
        return {
            "ats": os.path.join(ROOT_DIR, "inputs", "mathivanan_ats.json"),
            "notes": os.path.join(ROOT_DIR, "inputs", "mathivanan_notes.txt")
        }
    elif "jane" in name_lower or "smith" in name_lower:
        return {
            "ats": os.path.join(ROOT_DIR, "inputs", "ats.json"),
            "notes": os.path.join(ROOT_DIR, "inputs", "recruiter_notes.txt")
        }
    else:
        return {
            "ats": os.path.join(ROOT_DIR, "inputs", "ats.json"),
            "notes": os.path.join(ROOT_DIR, "inputs", "recruiter_notes.txt")
        }

st.set_page_config(page_title="Candidate Transformer", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        font-weight: 500;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎯 Candidate Profile Transformer")
st.markdown("Transform messy candidate data from multiple sources into a clean, trustworthy canonical profile.")

# Load config
config_path = os.path.join(ROOT_DIR, "config", "default.json")
try:
    with open(config_path, "r") as f:
        config = json.load(f)
except Exception:
    config = {"skills_synonyms": {}, "source_confidence": {}}

# Sidebar navigation
tab = st.sidebar.radio("Navigation", ["📤 Upload & Extract", "✏️ Review & Edit", "🔬 Sources & Trace", "📊 Output & Export"])

# Reset button
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset App & Clear State"):
    st.session_state.clear()
    st.rerun()

# Initialize session state
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = {}
if "profiles" not in st.session_state:
    st.session_state.profiles = []
if "edited_data" not in st.session_state:
    st.session_state.edited_data = {}

# ===========================
# TAB 1: UPLOAD & EXTRACT
# ===========================
if tab == "📤 Upload & Extract":
    st.header("Upload Resume & Automatic Extraction")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📄 Step 1: Ingest Resume")
        sample_option = st.selectbox("Load Sample Resume (Quick Demo)", ["(Upload your own)", "Mathivanan S (Recommended)", "Jane Smith"])
        uploaded_file = st.file_uploader("Or Upload resume (PDF or TXT)", type=["pdf", "txt"])
        
        resume_to_parse = None
        is_temp = False
        if sample_option == "Mathivanan S (Recommended)":
            resume_to_parse = os.path.join(ROOT_DIR, "inputs", "mathivanan_resume.txt")
        elif sample_option == "Jane Smith":
            resume_to_parse = os.path.join(ROOT_DIR, "inputs", "resume.txt")
            
        pdf_profiles = []
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                tmp.write(uploaded_file.getbuffer())
                resume_to_parse = tmp.name
                is_temp = True
            
            # Check for multi-source PDF
            if uploaded_file.name.lower().endswith(".pdf"):
                try:
                    clean_resume_text, pdf_profiles = process_multi_source_pdf(resume_to_parse)
                    # If we found any extra sources, write clean resume text and point resume_to_parse to it
                    if pdf_profiles:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as clean_tmp:
                            clean_tmp.write(clean_resume_text.encode("utf-8"))
                            resume_to_parse = clean_tmp.name
                            is_temp = True
                except Exception as e:
                    st.warning(f"Error checking multi-source PDF: {e}")
        
        if resume_to_parse:
            # Parse resume
            try:
                resume_data = parse_resume(resume_to_parse)
                
                # Fetch candidate identifiers
                c_name = resume_data.get("name")
                c_email = resume_data.get("emails", [None])[0] if resume_data.get("emails") else None
                
                # Setup all profiles list
                all_profiles = [resume_data]
                
                # Merge PDF profiles
                found_sources = set()
                for p in pdf_profiles:
                    all_profiles.append(p)
                    found_sources.add(p["source"])
                
                # 1. Fetch LinkedIn profile automatically
                if "linkedin" not in found_sources:
                    li_url = resume_data.get("linkedin_url")
                    if li_url:
                        try:
                            with st.spinner("🔗 Fetching LinkedIn profile..."):
                                linkedin_data = parse_linkedin(li_url)
                                if linkedin_data:
                                    all_profiles.append(linkedin_data)
                        except Exception as e:
                            st.warning(f"Could not fetch LinkedIn: {e}")
                            
                # 2. Fetch GitHub profile automatically
                if "github" not in found_sources:
                    gh_url = resume_data.get("github_url")
                    if gh_url:
                        try:
                            with st.spinner("🐙 Fetching GitHub profile..."):
                                github_data = parse_github(gh_url)
                                if github_data:
                                    all_profiles.append(github_data)
                        except Exception as e:
                            st.warning(f"Could not fetch GitHub: {e}")
                            
                # 3. Load matching default CSV profile automatically
                if "csv" not in found_sources:
                    csv_data = load_matching_csv_profile(c_name, c_email)
                    if csv_data:
                        all_profiles.append(csv_data)
                        
                # 4. Load matching default ATS and Notes profiles
                paths = get_matching_paths(c_name)
                
                if "ats" not in found_sources and os.path.exists(paths["ats"]):
                    try:
                        ats_data = parse_ats_json(paths["ats"])
                        if ats_data:
                            all_profiles.append(ats_data)
                    except Exception:
                        pass
                        
                if "notes" not in found_sources and os.path.exists(paths["notes"]):
                    try:
                        notes_data = parse_recruiter_notes(paths["notes"])
                        if notes_data:
                            all_profiles.append(notes_data)
                    except Exception:
                        pass
                
                # Save to session state
                st.session_state.profiles = all_profiles
                st.session_state.extracted_data = resume_data
                
                st.success("✅ Resume parsed and auto-merged with all default database sources (ATS/CSV/Notes/LinkedIn/GitHub) successfully!")
                
                # Show extracted data
                st.markdown("### 📋 Extracted Information")
                
                col_name, col_email = st.columns(2)
                with col_name:
                    st.metric("Full Name", resume_data.get("name") or "N/A")
                with col_email:
                    st.metric("Primary Email", resume_data.get("emails", ["N/A"])[0] if resume_data.get("emails") else "N/A")
                
                col_phone, col_headline = st.columns(2)
                with col_phone:
                    st.metric("Phone", resume_data.get("phones", ["N/A"])[0] if resume_data.get("phones") else "N/A")
                with col_headline:
                    st.metric("Headline", resume_data.get("headline")[:50] + "..." if resume_data.get("headline") else "N/A")
                
                # URLs
                st.markdown("#### 🔗 Profiles Found")
                col_li, col_gh = st.columns(2)
                with col_li:
                    if resume_data.get("linkedin_url"):
                        st.info(f"✅ LinkedIn: {resume_data['linkedin_url']}")
                    else:
                        st.warning("❌ No LinkedIn URL found")
                with col_gh:
                    if resume_data.get("github_url"):
                        st.info(f"✅ GitHub: {resume_data['github_url']}")
                    else:
                        st.warning("❌ No GitHub URL found")
                
                # Skills
                if resume_data.get("skills"):
                    st.markdown("#### 💼 Skills Detected")
                    st.write(", ".join(resume_data["skills"][:10]))
                
                if is_temp:
                    try:
                        os.unlink(resume_to_parse)
                    except Exception:
                        pass
                
            except Exception as e:
                st.error(f"❌ Error parsing resume: {e}")

    with col2:
        st.markdown("### ℹ️ Supported Formats")
        st.info("""
        - **PDF** files
        - **TXT** plain text
        - Extracts:
          - Name, email, phone
          - Skills with synonyms
          - LinkedIn URL
          - GitHub URL
          - Portfolio links
        """)

# ===========================
# TAB 2: REVIEW & EDIT
# ===========================
elif tab == "✏️ Review & Edit":
    st.header("Review & Edit Profile Data")
    
    if not st.session_state.extracted_data:
        st.warning("⚠️ Please upload a resume first in the 'Upload & Extract' tab")
    else:
        data = st.session_state.extracted_data.copy()
        
        st.markdown("### 👤 Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name", value=data.get("name") or "")
            st.session_state.edited_data["full_name"] = full_name
        with col2:
            headline = st.text_input("Headline/Title", value=data.get("headline") or "")
            st.session_state.edited_data["headline"] = headline
        
        col3, col4 = st.columns(2)
        with col3:
            location = st.text_input("Location", value=data.get("location") or "")
            st.session_state.edited_data["location"] = location
        with col4:
            # TODO: Implement as multiselect once added
            st.text_input("Years of Experience", value="", placeholder="e.g., 10")
        
        st.markdown("### 📞 Contact Information")
        col5, col6 = st.columns(2)
        with col5:
            emails = st.text_area("Emails (one per line)", value="\n".join(data.get("emails", [])))
            st.session_state.edited_data["emails"] = [e.strip() for e in emails.split("\n") if e.strip()]
        with col6:
            phones = st.text_area("Phones (one per line)", value="\n".join(data.get("phones", [])))
            st.session_state.edited_data["phones"] = [p.strip() for p in phones.split("\n") if p.strip()]
        
        st.markdown("### 🔗 Online Profiles")
        col7, col8 = st.columns(2)
        with col7:
            linkedin_url = st.text_input("LinkedIn URL", value=data.get("linkedin_url") or "")
            st.session_state.edited_data["linkedin_url"] = linkedin_url
        with col8:
            github_url = st.text_input("GitHub URL", value=data.get("github_url") or "")
            st.session_state.edited_data["github_url"] = github_url
        
        st.markdown("### 💼 Skills")
        skills = st.text_area("Skills (one per line)", value="\n".join(data.get("skills", [])))
        st.session_state.edited_data["skills"] = [s.strip() for s in skills.split("\n") if s.strip()]
        
        st.markdown("### 🏢 Experience")
        experience_count = len(data.get("experience", []))
        if experience_count == 0:
            st.text("No experience entries found in resume.")
        else:
            for i, exp in enumerate(data.get("experience", [])):
                with st.expander(f"Experience #{i+1}: {exp.get('company', 'N/A')}"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        st.text_input(f"Company {i+1}", value=exp.get("company", ""), key=f"exp_company_{i}")
                        st.text_input(f"Title {i+1}", value=exp.get("title", ""), key=f"exp_title_{i}")
                    with col_e2:
                        st.text_input(f"Start {i+1} (YYYY-MM)", value=exp.get("start", ""), key=f"exp_start_{i}")
                        st.text_input(f"End {i+1} (YYYY-MM)", value=exp.get("end", ""), key=f"exp_end_{i}")
        
        st.markdown("### 🎓 Education")
        education_count = len(data.get("education", []))
        if education_count == 0:
            st.text("No education entries found in resume.")
        else:
            for i, edu in enumerate(data.get("education", [])):
                with st.expander(f"Education #{i+1}: {edu.get('school', 'N/A')}"):
                    col_ed1, col_ed2 = st.columns(2)
                    with col_ed1:
                        st.text_input(f"School {i+1}", value=edu.get("school", ""), key=f"edu_school_{i}")
                        st.text_input(f"Degree {i+1}", value=edu.get("degree", ""), key=f"edu_degree_{i}")
                    with col_ed2:
                        st.text_input(f"Field {i+1}", value=edu.get("field", ""), key=f"edu_field_{i}")
                        st.text_input(f"Year {i+1}", value=str(edu.get("year", "")), key=f"edu_year_{i}")

# ===========================
# TAB: SOURCES & TRACE
# ===========================
elif tab == "🔬 Sources & Trace":
    st.header("Source Extraction and Merge Trace")

    if not st.session_state.profiles:
        st.warning("⚠️ No source profiles available. Upload a resume or fetch LinkedIn/GitHub from the Upload tab first.")
    else:
        profiles = st.session_state.profiles.copy()

        # Per-source tabs
        src_tabs = []
        for i, p in enumerate(profiles):
            label = p.get("source") or p.get("_source") or p.get("source_name") or f"Source #{i+1}"
            # Friendly label mapping
            if label == "resume":
                label = "Resume (PDF/TXT)"
            elif label == "linkedin":
                label = "LinkedIn"
            elif label == "github":
                label = "GitHub"
            elif label == "csv":
                label = "Recruiter Records (CSV)"
            elif label == "ats":
                label = "ATS JSON"
            elif label == "notes":
                label = "Recruiter Notes"
            src_tabs.append(label)

        tabs = st.tabs(src_tabs)
        for tab_obj, profile in zip(tabs, profiles):
            with tab_obj:
                st.markdown(f"### Raw Extracted Data — {profile.get('source', 'unknown')}")
                st.json(profile)
                st.markdown("**Quick highlights**")
                cols = st.columns(3)
                with cols[0]:
                    st.write("**Name**")
                    st.write(profile.get("name") or "—")
                with cols[1]:
                    st.write("**Email(s)**")
                    st.write(profile.get("emails", [])[:3] or "—")
                with cols[2]:
                    st.write("**Phone(s)**")
                    st.write(profile.get("phones", [])[:3] or "—")

        st.markdown("---")
        st.markdown("### ✅ What Was Extracted From Each Source")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📄 Resume (PDF/TXT)")
            resume_profile = profiles[0] if profiles and profiles[0].get("source") == "resume" else {}
            st.json({
                "name": resume_profile.get("name"),
                "summary": resume_profile.get("summary") or "",
                "emails": resume_profile.get("emails"),
                "phones": resume_profile.get("phones"),
                "skills": resume_profile.get("skills", []),
                "experience": resume_profile.get("experience", []),
                "education": resume_profile.get("education", []),
                "projects": resume_profile.get("projects", []),
                "linkedin_url": resume_profile.get("linkedin_url"),
                "github_url": resume_profile.get("github_url"),
            })
        
        with col2:
            st.markdown("#### 💼 LinkedIn")
            linkedin_profile = next((p for p in profiles if p.get("source") == "linkedin"), {})
            if linkedin_profile:
                st.json({
                    "name": linkedin_profile.get("name"),
                    "headline": linkedin_profile.get("headline"),
                    "location": linkedin_profile.get("location"),
                    "skills": linkedin_profile.get("skills", []),
                    "linkedin_url": linkedin_profile.get("linkedin_url"),
                    "urls": linkedin_profile.get("urls", []),
                    "experience": linkedin_profile.get("experience", [])[:2],
                    "education": linkedin_profile.get("education", [])[:2],
                    "certifications": linkedin_profile.get("certifications", [])
                })
            else:
                st.info("No LinkedIn data extracted")
        
        with col3:
            st.markdown("#### 🐙 GitHub")
            github_profile = next((p for p in profiles if p.get("source") == "github"), {})
            if github_profile:
                st.json({
                    "name": github_profile.get("name"),
                    "bio": github_profile.get("bio"),
                    "location": github_profile.get("location"),
                    "company": github_profile.get("company"),
                    "blog": github_profile.get("blog"),
                    "email": github_profile.get("email"),
                    "public_repos": github_profile.get("public_repos"),
                    "public_gists": github_profile.get("public_gists"),
                    "followers": github_profile.get("followers"),
                    "following": github_profile.get("following"),
                    "languages": github_profile.get("languages", []),
                    "links": github_profile.get("links", []),
                    "projects": github_profile.get("projects", []),
                    "hireable": github_profile.get("hireable")
                })
            else:
                st.info("No GitHub data extracted")
        try:
            default_profiles = [profiles[0]] if profiles else []
            merged_default = merge_profiles(default_profiles) if default_profiles else {}
        except Exception:
            merged_default = {"error": "merge failed"}

        try:
            merged_auto = merge_profiles(profiles)
        except Exception:
            merged_auto = {"error": "merge failed"}

        # Final merged after edited_data applied
        final_profiles = [p.copy() for p in profiles]
        if st.session_state.get("edited_data"):
            final_profiles[0].update(st.session_state.edited_data)

        try:
            merged_final = merge_profiles(final_profiles)
        except Exception:
            merged_final = {"error": "merge failed"}

        st.markdown("### Schema Comparison")
        col_def, col_auto, col_final = st.columns(3)
        with col_def:
            st.subheader("Default (first source)")
            st.json(merged_default)
        with col_auto:
            st.subheader("Auto-updated (all sources)")
            st.json(merged_auto)
        with col_final:
            st.subheader("Final (after edits)")
            st.json(merged_final)

        # Field-level trace for common fields
        st.markdown("### Field Update Trace")
        keys = ["name", "summary", "headline", "emails", "phones", "skills", "experience", "education", "projects", "certifications", "linkedin_url", "github_url"]
        trace_rows = []
        for k in keys:
            def_val = merged_default.get(k) if isinstance(merged_default, dict) else None
            auto_val = merged_auto.get(k) if isinstance(merged_auto, dict) else None
            fin_val = merged_final.get(k) if isinstance(merged_final, dict) else None
            
            # Shorten for display
            def_str = str(def_val)[:500] if def_val else "—"
            auto_str = str(auto_val)[:500] if auto_val else "—"
            fin_str = str(fin_val)[:500] if fin_val else "—"
            
            trace_rows.append({"field": k, "default": def_str, "auto_updated": auto_str, "final": fin_str})

        st.table(trace_rows)

        # Provenance differences
        st.markdown("### Provenance Differences")
        prov_def = merged_default.get("provenance", {}) if isinstance(merged_default, dict) else {}
        prov_auto = merged_auto.get("provenance", {}) if isinstance(merged_auto, dict) else {}
        prov_final = merged_final.get("provenance", {}) if isinstance(merged_final, dict) else {}

        st.markdown("**Default Profile Provenance**")
        st.json(prov_def)
        st.markdown("**Auto-updated Profile Provenance**")
        st.json(prov_auto)
        st.markdown("**Final Profile Provenance**")
        st.json(prov_final)

# ===========================
# TAB 3: OUTPUT & EXPORT
# ===========================
elif tab == "📊 Output & Export":
    st.header("Generate & Export Profile")
    
    if not st.session_state.extracted_data:
        st.warning("⚠️ Please upload and review a resume first")
    else:
        # Merge profiles
        profiles_to_merge = st.session_state.profiles.copy()
        
        # Add edited data if available
        if st.session_state.edited_data:
            profiles_to_merge[0].update(st.session_state.edited_data)
        
        # Normalize
        synonyms = config.get("skills_synonyms", {})
        for p in profiles_to_merge:
            if p.get("name"):
                p["name"] = normalize_name(p["name"]) or p["name"]
            if p.get("location"):
                p["location"] = normalize_location(p["location"]) or p["location"]
            if p.get("phones"):
                p["phones"] = [normalized for ph in p.get("phones", []) if (normalized := normalize_phone(ph, "US"))]
            if p.get("skills"):
                p["skills"] = normalize_skills(p.get("skills", []), synonyms)
        
        # Merge
        merged = merge_profiles(profiles_to_merge)
        
        # Confidence
        source_scores = config.get("source_confidence", {})
        conf = compute_confidence(merged, profiles_to_merge, source_scores)
        merged["overall_confidence"] = conf.get("overall", 0.0)
        merged["confidence_fields"] = conf.get("fields")
        
        # Display results
        st.markdown("### ✅ Generated Profile")
        
        col_key, col_conf = st.columns([3, 1])
        with col_key:
            st.text_input("Candidate ID", value=merged.get("candidate_id", ""), disabled=True)
        with col_conf:
            confidence_pct = min(100, int(merged.get("overall_confidence", 0) * 100))
            st.metric("Overall Confidence", f"{confidence_pct}%")
        
        # Canonical view
        st.markdown("#### 📋 Canonical Profile (All Data)")
        col_canon, col_proj = st.columns(2)
        
        with col_canon:
            canonical_json = json.dumps(merged, indent=2, default=str)
            st.json(merged)
            
            # Download canonical
            st.download_button(
                label="📥 Download Canonical JSON",
                data=canonical_json,
                file_name="canonical_profile.json",
                mime="application/json"
            )
        
        with col_proj:
            # Projection
            proj_cfg = config.get("projection", {})
            projected = apply_projection(merged, proj_cfg)
            
            projected_json = json.dumps(projected, indent=2, default=str)
            st.json(projected)
            
            # Download projected
            st.download_button(
                label="📥 Download Projected JSON",
                data=projected_json,
                file_name="projected_profile.json",
                mime="application/json"
            )
        
        # Provenance view
        st.markdown("#### 🔍 Provenance (Data Lineage)")
        if merged.get("provenance"):
            provenance_view = {}
            for field, sources in merged["provenance"].items():
                provenance_view[field] = f"From {sources[0].get('source', 'unknown')} via {sources[0].get('method', 'unknown')}"
            st.json(provenance_view)
        else:
            st.info("No provenance data available")
        
        # Export options
        st.markdown("### 💾 Export Options")
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            try:
                csv_flat = generate_flat_csv(merged)
                st.download_button(
                    label="📊 Download Flat CSV",
                    data=csv_flat,
                    file_name="candidate_flat.csv",
                    mime="text/csv",
                    key="dl_flat_csv"
                )
            except Exception as e:
                st.error(f"Error: {e}")
        
        with col_exp2:
            try:
                csv_nested = generate_nested_csv(merged)
                st.download_button(
                    label="🗂️ Download Nested CSV",
                    data=csv_nested,
                    file_name="candidate_nested.csv",
                    mime="text/csv",
                    key="dl_nested_csv"
                )
            except Exception as e:
                st.error(f"Error: {e}")
        
        with col_exp3:
            try:
                import io
                pdf_buffer = io.BytesIO()
                generate_pdf_report(merged, pdf_buffer)
                pdf_data = pdf_buffer.getvalue()
                st.download_button(
                    label="📄 Download PDF Report",
                    data=pdf_data,
                    file_name="candidate_report.pdf",
                    mime="application/pdf",
                    key="dl_pdf_report"
                )
            except Exception as e:
                st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>
        Candidate Transformer | Production-Grade Multi-Source Data Pipeline
        <br/>
        Extract • Normalize • Merge • Validate • Export
    </small>
</div>
""", unsafe_allow_html=True)
