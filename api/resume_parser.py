import pdfplumber
import docx
import os
import re
import google.generativeai as genai
import json

# ===============================
# CONFIGURATION & AI SETUP
# ===============================
# This pulls the key you set in the Vercel Dashboard
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# ===============================
# TEXT EXTRACTION FUNCTIONS
# ===============================
def extract_text_from_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        return " ".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""

def extract_text_from_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading TXT: {e}")
        return ""

# ===============================
# CLEAN TEXT
# ===============================
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ===============================
# GEMINI AI EXTRACTION LOGIC
# ===============================
def extract_info_with_gemini(text):
    """
    Sends resume text to Gemini to extract skills and experience level.
    """
    prompt = f"""
    You are an expert HR recruitment AI. Analyze the following resume text and extract:
    1. A comprehensive list of technical and soft skills.
    2. The career experience level (choose strictly one: Entry, Mid, or Senior).
    
    Return the response ONLY in valid JSON format:
    {{
        "skills": ["Skill1", "Skill2", ...],
        "experience_level": "Level"
    }}

    Resume Text:
    {text[:5000]}
    """

    try:
        response = model.generate_content(prompt)
        # Remove markdown code blocks if Gemini includes them
        clean_json = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_json)
    except Exception as e:
        print(f"⚠️ Gemini AI Error: {e}. Falling back to defaults.")
        return {
            "skills": ["General Professional"], 
            "experience_level": "Mid"
        }

# ===============================
# MAIN PARSE FUNCTION
# ===============================
def parse_resume(file_path):
    """
    The main function called by app.py
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

    # MAGIC HAPPENS HERE: Use AI to find skills instead of a hardcoded list
    ai_results = extract_info_with_gemini(cleaned_text)

    return {
        "resume_text": raw_text, # Original text for context
        "cleaned_text": cleaned_text,
        "skills": ai_results.get("skills", []),
        "experience_level": ai_results.get("experience_level", "Mid")
    }
