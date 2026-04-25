from dotenv import load_dotenv
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import random
import google.generativeai as genai

base_path = Path(__file__).resolve().parent
env_path = base_path.parent / '.env'
load_dotenv(dotenv_path=env_path)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# ===============================
# IMPORT PROJECT MODULES
# ===============================
from resume_parser import parse_resume
from job_matching import load_models_and_data, recommend_jobs
from ats_scoring import calculate_ats_score
from interview_module import get_interview_questions

# ===============================
# FLASK APP CONFIGURATION
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
UPLOAD_DIR = "/tmp"

app = Flask(
    __name__,
    template_folder=FRONTEND_DIR,
    static_folder=FRONTEND_DIR
)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ===============================
# FILE UPLOAD CONFIG
# ===============================
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ===============================
# HELPER FUNCTIONS
# ===============================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ===============================
# LOAD JOB MODELS ONCE
# ===============================
try:
    df_jobs, tfidf_vectorizer, tfidf_matrix = load_models_and_data()
    # CRITICAL: Fill NaNs immediately after loading to prevent API crashes
    if df_jobs is not None:
        df_jobs = df_jobs.fillna("N/A")
    print("✅ Job models loaded successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not load job models: {e}")
    df_jobs, tfidf_vectorizer, tfidf_matrix = None, None, None

# ===============================
# FRONTEND ROUTES
# ===============================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload")
def upload_page():
    return render_template("upload.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/builder")
def builder():
    return render_template("builder.html")

@app.route("/interview")
def interview():
    return render_template("interview.html")

@app.route("/login")
def login():
    # Redirect directly to dashboard (no login page)
    from flask import redirect
    return redirect("/dashboard")

@app.route("/<path:filename>")
def serve_static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# ===============================
# API ROUTES
# ===============================
@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    try:
        if "resume" not in request.files:
            return jsonify({"success": False, "error": "No resume uploaded"}), 400

        file = request.files["resume"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Only PDF, DOCX, or TXT allowed"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # 1. PARSE RESUME
        parsed_data = parse_resume(filepath)
        resume_experience = parsed_data.get("experience_level", "Mid")
        resume_skills = parsed_data.get("skills", [])
        resume_text = parsed_data.get("resume_text", "")

        # 2. GET RECOMMENDATIONS FIRST
        recommended_jobs = []
        if df_jobs is not None:
            recommended_jobs = recommend_jobs(
                resume_skills,
                tfidf_vectorizer,
                tfidf_matrix,
                df_jobs,
                top_n=5
            )

        # 3. CALCULATE ATS SCORE (Against the top recommendation, not just index 0)
        top_job = recommended_jobs[0] if recommended_jobs else {}
        
        ats_result = calculate_ats_score(
            resume_text,
            resume_skills,
            resume_experience,
            top_job
        )

        # 4. GENERATE IMPROVEMENTS (Logic remains the same)
        improvements = []
        if ats_result["skill_match"] < 60:
            improvements.append({"title": "Skill Gap", "description": "Add more technical keywords."})
        # ... [Add your other improvement checks here] ...

        return jsonify({
            "success": True,
            "skills": resume_skills,
            "experience_level": resume_experience,
            "ats_score": ats_result["ats_score"],
            "recommended_jobs": recommended_jobs,
            "ats_breakdown": ats_result,
            "improvements": improvements[:4]
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/job_recommendations", methods=["POST"])
def job_recommendations():
    # ... [Keep your existing logic, it's good!] ...
    # Just ensure you use the .fillna() data we set globally.
    pass

@app.route("/api/jobs/all", methods=["GET"])
def get_all_jobs():
    try:
        if df_jobs is None:
            return jsonify({"success": False, "error": "Job data not loaded"}), 500
        # Send 50 jobs, but drop the 'combined_text' to save bandwidth/RAM
        jobs = df_jobs.drop(columns=['combined_text']).head(50).to_dict("records")
        return jsonify({"success": True, "jobs": jobs}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/get_questions", methods=["POST"])
def fetch_questions():
    """
    Fetches questions based on the job title.
    Matches the 'Interview Prep' button on your frontend.
    """
    try:
        data = request.get_json()
        
        # Get the job title from the recommendation result or UI
        job_title = data.get("job_title", "Web Developer")
        
        # Call the logic from interview_module.py
        # It handles: Dictionary lookup -> Gemini AI fallback
        questions = get_interview_questions(job_title)
        
        return jsonify({
            "success": True, 
            "job_title": job_title,
            "questions": questions
        }), 200
        
    except Exception as e:
        print(f"Error fetching questions: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ===============================
# HEALTH CHECK
# ===============================
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "ONLYJOBS backend is running",
        "models_loaded": df_jobs is not None
    }), 200

# ===============================
# ERROR HANDLERS
# ===============================
@app.errorhandler(413)
def file_too_large(error):
    return jsonify({"success": False, "error": "File too large (Max 10MB)"}), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Route not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500

# ===============================
# RUN APPLICATION
# ===============================
if __name__ == "__main__":
    print("\n🚀 ONLYJOBS SERVER STARTED")
    print("🌐 http://127.0.0.1:5000")
    print("📁 Frontend:", FRONTEND_DIR)
    print("📤 Uploads:", UPLOAD_DIR)
    print("\nAvailable Routes:")
    print("GET  /")
    print("GET  /upload")
    print("GET  /dashboard")
    print("GET  /builder")
    print("POST /upload_resume")         # For the initial analysis
    print("POST /job_recommendations")   # For the detailed job matching
    print("POST /get_questions")         # The NEW consolidated interview route
    print("GET  /api/jobs/all")          # For the Jobs tab
    print("GET  /api/health\n")

    app.run(debug=True, host="0.0.0.0", port=5000)