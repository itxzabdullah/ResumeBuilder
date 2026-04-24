import re
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# ============================================
# TEXT CLEANING
# ============================================
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text

# ============================================
# SKILL MATCH SCORE (50%)
# ============================================
def skill_match_score(resume_skills, job_skills):
    """
    Computes percentage of job skills matched by resume skills
    resume_skills: list[str]
    job_skills: str, comma-separated
    """
    if not isinstance(job_skills, str) or not job_skills.strip():
        return 0

    resume_set = set(s.lower() for s in resume_skills)
    job_set = set(s.strip().lower() for s in job_skills.split(","))

    matched = resume_set.intersection(job_set)
    return (len(matched) / len(job_set)) * 100

# ============================================
# TEXT SIMILARITY SCORE (30%)
# ============================================
def text_similarity_score(resume_text, job_text):
    """
    Computes TF-IDF cosine similarity between resume text and job description
    """
    resume_text = clean_text(resume_text)
    job_text = clean_text(job_text)

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([resume_text, job_text])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    return similarity * 100

# ============================================
# EXPERIENCE MATCH SCORE (20%)
# ============================================
def experience_score(resume_experience, job_experience):
    """
    Scores experience alignment between resume and job
    Both must be one of: Entry, Mid, Senior
    """
    mapping = {
        "entry": 1,
        "mid": 2,
        "senior": 3
    }

    r = mapping.get(str(resume_experience).lower(), 2)
    j = mapping.get(str(job_experience).lower(), 2)

    diff = abs(r - j)

    if diff == 0:
        return 100
    elif diff == 1:
        return 70
    else:
        return 40

# ============================================
# FINAL ATS SCORE
# ============================================
def calculate_ats_score(resume_text, resume_skills, resume_experience, job):
    """
    Calculates weighted ATS score
    """
    skill_score = skill_match_score(resume_skills, job.get("skills", ""))
    text_score = text_similarity_score(resume_text, job.get("combined_text", ""))
    exp_score = experience_score(resume_experience, job.get("Experience Level", "Mid"))

    final_score = 0.5 * skill_score + 0.3 * text_score + 0.2 * exp_score

    return {
        "ats_score": round(final_score, 2),
        "skill_match": round(skill_score, 2),
        "text_similarity": round(text_score, 2),
        "experience_match": round(exp_score, 2)
    }
