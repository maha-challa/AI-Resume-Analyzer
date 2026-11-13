import re
from io import BytesIO
import PyPDF2

# Predefined dictionary of technical skills and their regex patterns.
# Key: Standardized display name
# Value: Regular expression pattern for accurate matching
SKILL_PATTERNS = {
    # Programming Languages
    "Python": r"\bpython\b",
    "Java": r"\bjava\b(?!script)",
    "JavaScript": r"\b(javascript|js|es6)\b",
    "TypeScript": r"\b(typescript|ts)\b",
    "C++": r"\b(c\+\+|cpp)\b",
    "C#": r"\b(c#|csharp)\b",
    "C": r"\b(c\s+language|c\s+programming)\b",
    "PHP": r"\bphp\b",
    "Ruby": r"\bruby\b",
    "Swift": r"\bswift\b",
    "Kotlin": r"\bkotlin\b",
    "Go / Golang": r"\b(golang|go\s+language)\b",
    "Rust": r"\brust\b",
    "R": r"\b(r\s+language|r\s+programming)\b",
    "Dart": r"\bdart\b",
    "Scala": r"\bscala\b",
    "Shell / Bash": r"\b(bash|shell\s+scripting|powershell)\b",

    # Web & Frontend Technologies
    "HTML": r"\b(html|html5)\b",
    "CSS": r"\b(css|css3)\b",
    "Bootstrap": r"\bbootstrap\b",
    "Tailwind CSS": r"\b(tailwind|tailwind\s*css)\b",
    "Sass / SCSS": r"\b(sass|scss)\b",
    "React": r"\b(react|react\.?js)\b",
    "Angular": r"\b(angular|angular\.?js)\b",
    "Vue.js": r"\b(vue|vue\.?js)\b",
    "Next.js": r"\b(next|next\.?js)\b",
    "Redux": r"\bredux\b",
    "jQuery": r"\bjquery\b",

    # Backend Frameworks
    "Flask": r"\bflask\b",
    "Django": r"\bdjango\b",
    "FastAPI": r"\bfastapi\b",
    "Node.js": r"\b(node|node\.?js)\b",
    "Express.js": r"\b(express|express\.?js)\b",
    "Spring Boot": r"\b(spring\s*boot|spring\s*framework)\b",
    "ASP.NET": r"\b(asp\.net|\.net\s*core)\b",
    "Ruby on Rails": r"\b(ruby\s*on\s*rails|rails)\b",
    "Laravel": r"\blaravel\b",

    # Databases & Storage
    "SQL": r"\bsql\b",
    "MySQL": r"\bmysql\b",
    "PostgreSQL": r"\b(postgresql|postgres)\b",
    "SQLite": r"\bsqlite\b",
    "MongoDB": r"\bmongodb\b",
    "Redis": r"\bredis\b",
    "Oracle DB": r"\boracle(?:\s*db|\s*database)?\b",
    "Microsoft SQL Server": r"\b(sql\s*server|mssql)\b",
    "Firebase": r"\bfirebase\b",
    "NoSQL": r"\bnosql\b",

    # Cloud & DevOps
    "AWS": r"\b(aws|amazon\s*web\s*services)\b",
    "Azure": r"\b(azure|microsoft\s*azure)\b",
    "Google Cloud (GCP)": r"\b(gcp|google\s*cloud)\b",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\b(kubernetes|k8s)\b",
    "CI/CD": r"\b(ci\s*/\s*cd|continuous\s*integration)\b",
    "Git": r"\bgit\b",
    "GitHub": r"\bgithub\b",
    "GitLab": r"\bgitlab\b",
    "Jenkins": r"\bjenkins\b",
    "Linux": r"\blinux\b",
    "Terraform": r"\bterraform\b",
    "Ansible": r"\bansible\b",

    # Data Science, AI & Machine Learning
    "Machine Learning": r"\b(machine\s*learning|ml)\b",
    "Deep Learning": r"\bdeep\s*learning\b",
    "Artificial Intelligence": r"\b(artificial\s*intelligence|ai)\b",
    "Natural Language Processing (NLP)": r"\b(nlp|natural\s*language\s*processing)\b",
    "Computer Vision": r"\bcomputer\s*vision\b",
    "Pandas": r"\bpandas\b",
    "NumPy": r"\bnumpy\b",
    "Scikit-learn": r"\b(scikit-?learn|sklearn)\b",
    "TensorFlow": r"\btensorflow\b",
    "PyTorch": r"\bpytorch\b",
    "OpenCV": r"\bopencv\b",
    "Matplotlib": r"\bmatplotlib\b",
    "Seaborn": r"\bseaborn\b",
    "Tableau": r"\btableau\b",
    "Power BI": r"\bpower\s*bi\b",

    # APIs, Protocols & Architecture
    "REST API": r"\b(rest|restful|rest\s*apis?)\b",
    "GraphQL": r"\bgraphql\b",
    "Microservices": r"\bmicroservices\b",
    "SOAP": r"\bsoap\b",
    "WebSockets": r"\bwebsockets?\b",
    "JSON": r"\bjson\b",

    # Methodologies & Tools
    "Agile / Scrum": r"\b(agile|scrum)\b",
    "Jira": r"\bjira\b",
    "Postman": r"\bpostman\b",
    "Unit Testing": r"\b(unit\s*testing|pytest|junit|jest)\b",
}


def extract_text_from_pdf(file_stream) -> str:
    """
    Extracts plain text from an uploaded PDF stream using PyPDF2.
    Handles multi-page documents and normalizes whitespace.
    """
    try:
        # Seek stream back to beginning in case it was previously read
        if hasattr(file_stream, "seek"):
            file_stream.seek(0)

        # In-memory stream handling
        reader = PyPDF2.PdfReader(file_stream)
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise ValueError("The uploaded PDF is password protected. Please upload an unprotected file.")

        extracted_pages = []
        for index, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text.strip())

        full_text = "\n".join(extracted_pages).strip()
        if not full_text:
            raise ValueError(
                "No readable text could be extracted from this PDF. "
                "It may be a scanned image or empty. Please ensure your PDF contains selectable text."
            )

        return full_text
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Unable to read the PDF file: {str(e)}")


def extract_skills(text: str) -> list:
    """
    Identifies technical skills from a block of text using regex keyword matching.
    Returns a sorted list of matched skill names.
    """
    if not text:
        return []

    found_skills = []
    # Case-insensitive search
    for skill_name, pattern in SKILL_PATTERNS.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            found_skills.append(skill_name)

    return sorted(found_skills, key=lambda s: s.lower())


def analyze_resume(resume_text: str, job_description: str) -> dict:
    """
    Compares skills in resume_text against required skills in job_description.
    Calculates a keyword-match estimate and generates improvement suggestions.
    """
    resume_skills = extract_skills(resume_text)
    required_skills = extract_skills(job_description)

    # Matched: Skills in BOTH resume and job description
    matched_skills = [skill for skill in required_skills if skill in resume_skills]

    # Missing: Skills in job description but NOT in resume
    missing_skills = [skill for skill in required_skills if skill not in resume_skills]

    # Additional: Skills in resume that were not specifically mentioned in the job description
    additional_skills = [skill for skill in resume_skills if skill not in required_skills]

    # Calculate match percentage
    if required_skills:
        match_percentage = round((len(matched_skills) / len(required_skills)) * 100, 1)
    elif resume_skills:
        # No specific technical skills found in job description, but resume has skills
        match_percentage = 100.0
    else:
        match_percentage = 0.0

    # Determine match rating badge and color
    if match_percentage >= 80:
        match_level = "High Match"
        match_color = "success"
    elif match_percentage >= 50:
        match_level = "Moderate Match"
        match_color = "warning"
    else:
        match_level = "Needs Optimization"
        match_color = "danger"

    # Generate tailored improvement suggestions
    suggestions = []

    if missing_skills:
        top_missing = missing_skills[:5]
        suggestions.append(
            f"Add high-priority missing skills: Focus on incorporating {', '.join(top_missing)} "
            "into your skills list, work experience, or personal projects."
        )
        suggestions.append(
            "Provide evidence: For each missing skill you possess, add bullet points showing "
            "how you used that technology to solve a problem or build a feature."
        )
    else:
        suggestions.append(
            "Great job! Your resume covers all the key technical skills detected in the job description."
        )

    if match_percentage < 70:
        suggestions.append(
            "Keyword alignment: Review the job description carefully and mirror its exact phrasing "
            "and terminology where applicable to your background."
        )

    suggestions.append(
        "Quantify your achievements: Enhance your bullet points with measurable outcomes "
        "(e.g., 'Improved performance by 25%' or 'Reduced API response times by 150ms')."
    )

    if additional_skills:
        suggestions.append(
            f"Bonus strengths detected: Your resume also highlights {', '.join(additional_skills[:4])}, "
            "which can give you a competitive edge."
        )

    return {
        "match_percentage": match_percentage,
        "match_level": match_level,
        "match_color": match_color,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "additional_skills": additional_skills,
        "resume_skills": resume_skills,
        "required_skills": required_skills,
        "suggestions": suggestions,
        "resume_text_preview": resume_text[:1000] + ("..." if len(resume_text) > 1000 else ""),
        "full_resume_text": resume_text,
    }

