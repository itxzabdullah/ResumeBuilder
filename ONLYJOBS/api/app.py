from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import random

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
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

app = Flask(
    __name__,
    template_folder=FRONTEND_DIR,
    static_folder=FRONTEND_DIR
)

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

# ===============================
# FILE UPLOAD CONFIG
# ===============================
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

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
            return jsonify({"success": False, "error": "Only PDF, DOCX, or TXT files are allowed"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # ===============================
        # PARSE RESUME
        # ===============================
        parsed_data = parse_resume(filepath)
        resume_experience = parsed_data.get("experience_level", "Mid")

        # ===============================
        # SAMPLE ATS SCORE (for demonstration)
        # ===============================
        sample_job = {
            "skills": "Python, Flask, SQL, Git, Docker, REST API, PostgreSQL",
            "combined_text": "Backend developer working with Flask and APIs. Strong experience in Python, database management, and cloud deployment.",
            "Experience Level": "Mid"
        }

        ats_result = calculate_ats_score(
            parsed_data.get("resume_text", ""),
            parsed_data.get("skills", []),
            resume_experience,
            sample_job
        )

        # ===============================
        # GENERATE IMPROVEMENTS
        # ===============================
        improvements = []

        if ats_result["skill_match"] < 50:
            improvements.append({
                "title": "Missing Key Skills",
                "description": f"Your resume matches only {ats_result['skill_match']}% of required skills. Add more relevant technical skills."
            })
        elif ats_result["skill_match"] < 70:
            improvements.append({
                "title": "Improve Skill Coverage",
                "description": "Consider adding more in-demand skills like Docker, Kubernetes, or cloud platforms (AWS/Azure)."
            })
        else:
            improvements.append({
                "title": "Excellent Skill Match",
                "description": f"Your resume shows {ats_result['skill_match']}% skill alignment. Great job!"
            })

        if ats_result["text_similarity"] < 40:
            improvements.append({
                "title": "Strengthen Job Relevance",
                "description": "Your resume content doesn't align well with job descriptions. Use more industry-standard terminology."
            })
        elif ats_result["text_similarity"] < 60:
            improvements.append({
                "title": "Enhance Content Alignment",
                "description": "Good start! Add more specific examples of projects and achievements that match typical job requirements."
            })

        if ats_result["experience_match"] < 70:
            improvements.append({
                "title": "Experience Level Mismatch",
                "description": "Your experience level may not align with target roles. Consider highlighting relevant projects and responsibilities."
            })

        if len(parsed_data.get("skills", [])) < 5:
            improvements.append({
                "title": "Add More Skills",
                "description": "Include at least 8-10 relevant technical and soft skills to improve ATS compatibility."
            })

        return jsonify({
            "success": True,
            "message": "Resume parsed successfully",
            "skills": parsed_data.get("skills", []),
            "resume_text": parsed_data.get("resume_text", ""),
            "experience_level": resume_experience,
            "ats_score": ats_result["ats_score"],
            "ats_breakdown": {
                "skill_match": ats_result["skill_match"],
                "text_similarity": ats_result["text_similarity"],
                "experience_match": ats_result["experience_match"]
            },
            "improvements": improvements[:4]
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ===============================
# JOB RECOMMENDATIONS ROUTE
# ===============================
@app.route("/job_recommendations", methods=["POST"])
def job_recommendations():
    try:
        if df_jobs is None or tfidf_vectorizer is None or tfidf_matrix is None:
            return jsonify({"success": False, "error": "Job matching models not loaded"}), 500

        data = request.get_json()

        resume_skills = data.get("skills", [])
        resume_text = data.get("resume_text", "")
        resume_experience = data.get("experience_level", "Mid")
        preferred_work_type = data.get("work_type", None)

        if not resume_skills:
            return jsonify({"success": False, "error": "Skills required"}), 400

        # Get top jobs from TF-IDF similarity
        matched_jobs = recommend_jobs(
            resume_skills,
            tfidf_vectorizer,
            tfidf_matrix,
            df_jobs,
            top_n=20
        )

        final_results = []

        for job in matched_jobs:
            # Filter by work type if specified
            if preferred_work_type:
                if job.get("Work Type", "").lower() != preferred_work_type.lower():
                    continue

            ats = calculate_ats_score(
                resume_text,
                resume_skills,
                resume_experience,
                job
            )

            similarity_score = job.get("similarity_score", 0)
            combined_score = 0.7 * ats["ats_score"] + 0.3 * similarity_score

            explanation = []
            if ats["skill_match"] < 50:
                explanation.append("Add more relevant skills.")
            elif ats["skill_match"] < 70:
                explanation.append("Good skill match, can improve coverage.")

            if ats["text_similarity"] < 50:
                explanation.append("Align resume text with job description.")

            if ats["experience_match"] < 70:
                explanation.append(f"Experience mismatch: resume ({resume_experience}) vs job ({job.get('Experience Level', 'Mid')})")

            final_results.append({
                "job_id": job.get("Job Id"),
                "job_title": job.get("Job Title"),
                "company": job.get("Company"),
                "location": job.get("location"),
                "work_type": job.get("Work Type"),
                "salary": job.get("Salary Range"),
                "ats_score": ats["ats_score"],
                "skill_match": ats["skill_match"],
                "text_similarity": ats["text_similarity"],
                "experience_match": ats["experience_match"],
                "similarity_score": similarity_score,
                "combined_score": round(combined_score, 2),
                "match_score": round(combined_score, 2),  # Add this for compatibility
                "explanation": explanation
            })

        # Sort by combined score
        final_results = sorted(final_results, key=lambda x: x["combined_score"], reverse=True)
        final_results = final_results[:10]

        return jsonify({
            "success": True,
            "recommended_jobs": final_results,  # Changed from 'results' to 'recommended_jobs'
            "count": len(final_results)
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/api/jobs/all", methods=["GET"])
def get_all_jobs():
    """Fetch all jobs for the dedicated 'Jobs' tab."""
    try:
        if df_jobs is None:
            return jsonify({"success": False, "error": "Job data not loaded"}), 500
            
        # Limiting to 50 jobs for demo purposes
        jobs = df_jobs.head(50).to_dict("records")
        return jsonify({"success": True, "jobs": jobs}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/interview_questions", methods=["POST"])
def fetch_questions():
    """Fetches questions based on the job title using interview_module.py."""
    try:
        data = request.json
        job_title = data.get("job_title", "Web Developer")
        questions = get_interview_questions(job_title)
        return jsonify({"success": True, "questions": questions}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ===============================
# INTERVIEW QUESTIONS ROUTE
# ===============================
@app.route("/interview_questions", methods=["POST"])
def interview_questions():
    try:
        data = request.get_json()

        job_title = data.get("job_title", "")
        role = data.get("role", "")

        if not job_title:
            return jsonify({"success": False, "error": "Job title required"}), 400

        questions = get_interview_questions(job_title, role)

        return jsonify({
            "success": True,
            "job_title": job_title,
            "questions": questions
        }), 200

    except Exception as e:
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
    print("GET  /login (redirects to /dashboard)")
    print("POST /upload_resume")
    print("POST /job_recommendations")
    print("POST /interview_questions")
    print("POST /api/interview_questions")
    print("GET  /api/jobs/all")
    print("GET  /api/health\n")

    app.run(debug=True, host="0.0.0.0", port=5000)