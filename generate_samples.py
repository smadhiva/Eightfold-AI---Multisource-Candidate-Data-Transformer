"""Generate sample PDF resume"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch


def generate_sample_resume():
    """Generate a sample resume PDF."""
    path = "inputs/resume.pdf"
    doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='black',
        spaceAfter=12,
        alignment=1,  # center
    )
    story.append(Paragraph("Jane Smith", title_style))
    story.append(Paragraph("jane.smith@techcorp.com | +1-415-987-6543 | San Francisco, CA", styles['Normal']))
    story.append(Paragraph("https://www.linkedin.com/in/janesmith | https://github.com/janesmith | https://janesmith.dev", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    # Professional Summary
    story.append(Paragraph("<b>Professional Summary</b>", styles['Heading2']))
    story.append(Paragraph(
        "Principal Engineer with 10+ years of experience in full-stack development, cloud architecture, and team leadership. "
        "Proven track record of scaling systems to handle millions of requests per day.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15*inch))

    # Experience
    story.append(Paragraph("<b>Experience</b>", styles['Heading2']))
    story.append(Paragraph("<b>Principal Engineer</b>, TechCorp (Jan 2020 - Present)", styles['Normal']))
    story.append(Paragraph(
        "• Led architecture redesign reducing latency by 40%<br/>"
        "• Managed team of 8 engineers across 3 continents<br/>"
        "• Implemented ML pipeline for customer insights",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("<b>Senior Software Engineer</b>, Acme Corp (Jun 2018 - Dec 2019)", styles['Normal']))
    story.append(Paragraph(
        "• Built distributed payment processing system handling $50M+ annually<br/>"
        "• Mentored 5 junior engineers<br/>"
        "• Reduced deployment time from 2 hours to 15 mins",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15*inch))

    # Skills
    story.append(Paragraph("<b>Skills</b>", styles['Heading2']))
    story.append(Paragraph(
        "<b>Languages:</b> Python, JavaScript, Go, SQL<br/>"
        "<b>Frameworks:</b> Django, React, FastAPI, Node.js<br/>"
        "<b>Cloud:</b> AWS (EC2, S3, Lambda), Kubernetes, Docker<br/>"
        "<b>Specialties:</b> System Design, Microservices, Database Optimization",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15*inch))

    # Education
    story.append(Paragraph("<b>Education</b>", styles['Heading2']))
    story.append(Paragraph("<b>B.S. Computer Science</b>, University of California, Berkeley (2014)", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))

    # Certifications
    story.append(Paragraph("<b>Certifications</b>", styles['Heading2']))
    story.append(Paragraph("• AWS Solutions Architect Professional (2021)<br/>• Kubernetes Application Developer (2020)", styles['Normal']))

    doc.build(story)
    print(f"Generated {path}")


if __name__ == "__main__":
    generate_sample_resume()
