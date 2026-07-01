import json
import csv
import io
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def export_json(obj: Dict[str, Any], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def generate_flat_csv(merged: Dict[str, Any]) -> str:
    """Generate flat CSV representation of profile."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Candidate ID", "Full Name", "Headline", "Location", 
        "Primary Email", "Primary Phone", "Skills", 
        "LinkedIn URL", "GitHub URL", "Overall Confidence"
    ])
    
    # Values
    email = merged.get("emails", [""])[0] if merged.get("emails") else ""
    phone = merged.get("phones", [""])[0] if merged.get("phones") else ""
    skills = ", ".join(merged.get("skills", []))
    
    writer.writerow([
        merged.get("candidate_id", ""),
        merged.get("full_name") or merged.get("name") or "",
        merged.get("headline") or "",
        merged.get("location") or "",
        email,
        phone,
        skills,
        merged.get("linkedin_url") or "",
        merged.get("github_url") or "",
        f"{int(merged.get('overall_confidence', 0) * 100)}%"
    ])
    return output.getvalue()

def generate_nested_csv(merged: Dict[str, Any]) -> str:
    """Generate nested CSV representation with serialized arrays."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Candidate ID", "Full Name", "Headline", "Location", 
        "Emails", "Phones", "Skills", "LinkedIn URL", "GitHub URL", 
        "Experience (JSON)", "Education (JSON)", "Projects (JSON)", 
        "Certifications (JSON)", "Overall Confidence"
    ])
    
    # Values
    emails = "; ".join(merged.get("emails", []))
    phones = "; ".join(merged.get("phones", []))
    skills = "; ".join(merged.get("skills", []))
    certs = "; ".join(merged.get("certifications", []))
    
    exp_json = json.dumps(merged.get("experience", []), default=str)
    edu_json = json.dumps(merged.get("education", []), default=str)
    proj_json = json.dumps(merged.get("projects", []), default=str)
    
    writer.writerow([
        merged.get("candidate_id", ""),
        merged.get("full_name") or merged.get("name") or "",
        merged.get("headline") or "",
        merged.get("location") or "",
        emails,
        phones,
        skills,
        merged.get("linkedin_url") or "",
        merged.get("github_url") or "",
        exp_json,
        edu_json,
        proj_json,
        certs,
        f"{int(merged.get('overall_confidence', 0) * 100)}%"
    ])
    return output.getvalue()

def generate_pdf_report(merged: Dict[str, Any], buffer) -> None:
    """Generate a premium styling candidate PDF profile report using ReportLab."""
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    primary_color = colors.HexColor("#1A365D")   # Sleek dark blue
    secondary_color = colors.HexColor("#2B6CB0") # Medium blue
    text_color = colors.HexColor("#2D3748")      # Dark gray text
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color
    )
    
    headline_style = ParagraphStyle(
        'DocHeadline',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=secondary_color
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_color
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6
    )
    
    story = []
    
    # Candidate Header
    story.append(Paragraph(merged.get("full_name") or merged.get("name") or "Unnamed Candidate", title_style))
    story.append(Spacer(1, 4))
    
    headline = merged.get("headline") or ""
    if headline:
        story.append(Paragraph(headline, headline_style))
        story.append(Spacer(1, 10))
        
    # Contact grid (using Table)
    contact_data = []
    emails = merged.get("emails", [])
    phones = merged.get("phones", [])
    loc = merged.get("location") or "N/A"
    
    email_str = emails[0] if emails else "N/A"
    phone_str = phones[0] if phones else "N/A"
    
    contact_data.append([
        Paragraph(f"<b>Email:</b> {email_str}", body_style),
        Paragraph(f"<b>Phone:</b> {phone_str}", body_style)
    ])
    
    li_url = merged.get("linkedin_url") or "N/A"
    gh_url = merged.get("github_url") or "N/A"
    
    contact_data.append([
        Paragraph(f"<b>Location:</b> {loc}", body_style),
        Paragraph(f"<b>Confidence Score:</b> {int(merged.get('overall_confidence', 0) * 100)}%", body_style)
    ])
    
    contact_data.append([
        Paragraph(f"<b>LinkedIn:</b> {li_url}", body_style),
        Paragraph(f"<b>GitHub:</b> {gh_url}", body_style)
    ])
    
    contact_table = Table(contact_data, colWidths=[260, 260])
    contact_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(contact_table)
    story.append(Spacer(1, 15))
    
    # Experience
    exps = merged.get("experience", [])
    if exps:
        story.append(Paragraph("Work Experience", h2_style))
        for exp in exps:
            comp = exp.get("company", "N/A")
            tit = exp.get("title", "N/A")
            start = exp.get("start") or "N/A"
            end = exp.get("end") or "Present"
            desc = exp.get("description") or ""
            
            exp_header = f"<b>{tit}</b> at <b>{comp}</b> ({start} - {end})"
            story.append(Paragraph(exp_header, body_style))
            if desc:
                story.append(Spacer(1, 2))
                story.append(Paragraph(desc, body_style))
            story.append(Spacer(1, 10))
            
    # Education
    edus = merged.get("education", [])
    if edus:
        story.append(Paragraph("Education", h2_style))
        for edu in edus:
            school = edu.get("school") or edu.get("institution") or "N/A"
            degree = edu.get("degree") or ""
            field = edu.get("field") or ""
            year = edu.get("year") or edu.get("end") or ""
            
            edu_str = f"<b>{degree} {f'in {field}' if field else ''}</b>"
            edu_details = f"{school} (Class of {year})" if year else school
            
            story.append(Paragraph(edu_str, body_style))
            story.append(Paragraph(edu_details, body_style))
            story.append(Spacer(1, 8))
            
    # Projects
    projs = merged.get("projects", [])
    if projs:
        story.append(Paragraph("Projects", h2_style))
        for proj in projs:
            title = proj.get("title", "Unnamed Project")
            desc = proj.get("description") or ""
            url = proj.get("url") or ""
            
            proj_header = f"<b>{title}</b>" + (f" — <font color='#2B6CB0'>{url}</font>" if url else "")
            story.append(Paragraph(proj_header, body_style))
            if desc:
                story.append(Spacer(1, 2))
                story.append(Paragraph(desc, body_style))
            story.append(Spacer(1, 8))
            
    # Certifications
    certs = merged.get("certifications", [])
    if certs:
        story.append(Paragraph("Licenses & Certifications", h2_style))
        cert_bullets = []
        for cert in certs:
            cert_bullets.append(Paragraph(f"• {cert}", body_style))
            
        cert_table_data = []
        # split into two columns
        for idx in range(0, len(cert_bullets), 2):
            col1_cert = cert_bullets[idx]
            col2_cert = cert_bullets[idx+1] if idx+1 < len(cert_bullets) else Paragraph("", body_style)
            cert_table_data.append([col1_cert, col2_cert])
            
        cert_table = Table(cert_table_data, colWidths=[260, 260])
        cert_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(cert_table)
        story.append(Spacer(1, 10))
        
    # Skills
    skills = merged.get("skills", [])
    if skills:
        story.append(Paragraph("Technical Skills", h2_style))
        skills_str = ", ".join(skills)
        story.append(Paragraph(skills_str, body_style))
        
    doc.build(story)
