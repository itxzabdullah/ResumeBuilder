import os
import pandas as pd
import pickle
import re
from sklearn.metrics.pairwise import cosine_similarity

# ============================================
# CONFIG
# ============================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(BASE_DIR, "data", "jobs_cleaned.csv")
VECTORIZER_PATH = os.path.join(BASE_DIR, "models", "tfidf_vectorizer.pkl")
MATRIX_PATH = os.path.join(BASE_DIR, "models", "tfidf_matrix.pkl")

# ============================================
# LOAD DATA + MODELS (ONCE)
# ============================================

def load_models_and_data():
    df = pd.read_csv(DATA_PATH)

    if "combined_text" not in df.columns:
        raise ValueError("combined_text column missing in dataset")

    with open(VECTORIZER_PATH, "rb") as f:
        tfidf_vectorizer = pickle.load(f)

    with open(MATRIX_PATH, "rb") as f:
        tfidf_matrix = pickle.load(f)

    return df, tfidf_vectorizer, tfidf_matrix


# ============================================
# CLEAN USER INPUT
# ============================================

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text


# ============================================
# JOB RECOMMENDATION LOGIC
# ============================================

def recommend_jobs(user_skills, tfidf_vectorizer, tfidf_matrix, df, top_n=5):
    """
    Returns FULL job rows + similarity_score
    """

    if isinstance(user_skills, list):
        user_text = " ".join(user_skills)
    else:
        user_text = user_skills

    user_text = clean_text(user_text)

    user_vector = tfidf_vectorizer.transform([user_text])
    similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()

    top_indices = similarities.argsort()[-top_n:][::-1]

    results = []
    for idx in top_indices:
        job = df.iloc[idx].to_dict()
        job["similarity_score"] = round(float(similarities[idx]) * 100, 2)
        results.append(job)

    return results
