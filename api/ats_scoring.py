import re
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# ============================================
# TEXT CLEANING
# ============================================
def clean_text(text):
    if not text: return ""
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text

# ============================================
# SKILL MATCH SCORE (50%)
# ============================================
def skill_match_score(resume_skills, job_skills_str):
    """
    resume_skills: list of strings from parser
    job_skills_str: The 'Job Description' or 'skills' column from CSV
    """
    if not job_skills_str or not resume_skills:
        return 0

    # Clean the job description to find skill matches
    job_text = str(job_skills_str).lower()
    resume_set = set(s.lower() for s in resume_skills)
    
    # Check how many extracted skills appear in the Job text
    matched = [s for s in resume_set if s in job_text]
    
    # Calculate score based on total skills extracted
    return (len(matched) / len(resume_set)) * 100 if resume_skills else 0

# ============================================
# TEXT SIMILARITY SCORE (30%)
# ============================================
def text_similarity_score(resume_text, job_text):
    """
    Optimized for Vercel: Uses a lightweight comparison
    """
    if not resume_text or not job_text:
        return 0
        
    resume_text = clean_text(resume_text)
    job_text = clean_text(job_text)

    # We use a single vectorizer call to save memory on Vercel
    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
        tfidf = vectorizer.fit_transform([resume_text, job_text])
        similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return similarity * 100
    except:
        return 50 # Fallback score

# ============================================
# EXPERIENCE MATCH SCORE (20%)
# ============================================
def experience_score(resume_experience, job_experience):
    mapping = {"entry": 1, "mid": 2, "senior": 3}

    r = mapping.get(str(resume_experience).lower(), 2)
    # Match the CSV column name exactly
    j = mapping.get(str(job_experience).lower(), 2)

    diff = abs(r - j)
    if diff == 0: return 100
    elif diff == 1: return 70
    else: return 40

# ============================================
# FINAL ATS SCORE
# ============================================
def calculate_ats_score(resume_text, resume_skills, resume_experience, job):
    """
    Calculates weighted ATS score using CSV columns
    """
    # Key Fix: Use 'Job Description' or 'Job Title' if 'skills' column doesn't exist
    job_desc = job.get("Job Description", job.get("skills", ""))
    
    skill_score = skill_match_score(resume_skills, job_desc)
    text_score = text_similarity_score(resume_text, job_desc)
    
    # Use 'Experience Level' to match your 10k dataset column name
    job_exp = job.get("Experience Level", "Mid")
    exp_score = experience_score(resume_experience, job_exp)

    final_score = (0.5 * skill_score) + (0.3 * text_score) + (0.2 * exp_score)

    return {
        "ats_score": round(final_score, 2),
        "skill_match": round(skill_score, 2),
        "text_similarity": round(text_score, 2),
        "experience_match": round(exp_score, 2)
    }