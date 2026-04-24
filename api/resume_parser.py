import pdfplumber
import docx
import os
import re
import spacy

# ===============================
# LOAD NLP MODEL
# ===============================
nlp = spacy.load("en_core_web_sm")

# ===============================
# SKILLS DATABASE (BASIC + EXTENDABLE)
# ===============================
SKILLS_DB = [
    "python", "java", "c++", "c#", "javascript", "typescript",
    "sql", "mysql", "postgresql", "mongodb",
    "machine learning", "deep learning", "data science",
    "flask", "django", "fastapi",
    "react", "angular", "node.js",
    "html", "css", "bootstrap",
    "git", "github", "docker", "kubernetes",
    "aws", "azure", "gcp",
    "linux", "api", "rest", "json"
]

# ===============================
# TEXT EXTRACTION FUNCTIONS
# ===============================
def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    return text


def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return " ".join([para.text for para in doc.paragraphs])


def extract_text_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ===============================
# CLEAN TEXT
# ===============================
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ===============================
# SKILL EXTRACTION
# ===============================
def extract_skills(text):
    found_skills = set()
    for skill in SKILLS_DB:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text):
            found_skills.add(skill)
    return sorted(found_skills)


# ===============================
# EXPERIENCE LEVEL EXTRACTION
# ===============================
def extract_experience_level(text):
    """
    Infer experience level from resume text
    Returns: Entry | Mid | Senior
    """

    text = text.lower()

    # Senior-level signals
    if re.search(r"\b(senior|lead|principal|architect|manager)\b", text):
        return "Senior"

    # Entry-level signals
    if re.search(r"\b(entry[-\s]?level|fresher|graduate|junior)\b", text):
        return "Entry"

    # Years of experience signals
    year_matches = re.findall(r"(\d+)\+?\s+years?", text)

    if year_matches:
        years = max(map(int, year_matches))

        if years <= 1:
            return "Entry"
        elif 2 <= years <= 4:
            return "Mid"
        else:
            return "Senior"

    # Safe default
    return "Mid"


# ===============================
# MAIN PARSE FUNCTION
# ===============================
def parse_resume(file_path):
    """
    Parse resume and extract text + skills + experience level

    Args:
        file_path (str): Path to uploaded resume

    Returns:
        dict: {
            'resume_text': str,
            'cleaned_text': str,
            'skills': list[str],
            'experience_level': str
        }
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError("Resume file not found")

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
    elif extension == ".docx":
        raw_text = extract_text_from_docx(file_path)
    elif extension == ".txt":
        raw_text = extract_text_from_txt(file_path)
    else:
        raise ValueError("Unsupported file format")

    cleaned_text = clean_text(raw_text)
    skills = extract_skills(cleaned_text)
    experience_level = extract_experience_level(cleaned_text)

    return {
        "resume_text": cleaned_text,
        "cleaned_text": cleaned_text,
        "skills": skills,
        "experience_level": experience_level
    }
