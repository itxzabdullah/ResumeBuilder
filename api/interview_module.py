import random
import os
import json
import google.generativeai as genai

# ===============================
# CONFIGURATION
# ===============================
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# -------------------------------
# 1. CACHED QUESTION BANK (Fast)
# -------------------------------
INTERVIEW_QUESTIONS = {
    "Frontend Web Developer": {
        "technical": [
            "Explain the difference between HTML, CSS, and JavaScript.",
            "How does React improve performance using Virtual DOM?",
            "What are responsive design principles?"
        ],
        "behavioral": ["Describe a time you worked with a designer.", "How do you handle tight deadlines?"],
        "situational": ["How would you fix a website that loads slowly?"]
    },
    "Web Developer": {
        "technical": ["What is REST API?", "Explain client-server architecture."],
        "behavioral": ["Describe a challenging project.", "How do you manage multiple tasks?"],
        "situational": ["How would you debug a broken web page?"]
    },
    # Add your other hardcoded roles here...
}

GENERIC_QUESTIONS = {
    "technical": ["Explain your technical skill set.", "What tools do you use?"],
    "behavioral": ["Tell me about yourself.", "What are your strengths?"],
    "situational": ["How do you handle pressure at work?"]
}

# -------------------------------
# 2. AI GENERATION LOGIC (Dynamic)
# -------------------------------
def generate_questions_with_ai(job_title):
    """Generates professional questions using Gemini for niche roles."""
    prompt = f"""
    Generate professional interview questions for: {job_title}.
    Provide exactly 3 technical, 3 behavioral, and 3 situational questions.
    Return the response ONLY in this valid JSON format:
    {{
        "technical": ["q1", "q2", "q3"],
        "behavioral": ["q1", "q2", "q3"],
        "situational": ["q1", "q2", "q3"]
    }}
    """
    try:
        response = model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text.strip())
    except Exception as e:
        print(f"AI Interview Error: {e}")
        return GENERIC_QUESTIONS

# -------------------------------
# 3. MAIN INTERFACE FUNCTION
# -------------------------------
def get_interview_questions(job_title, role=None, max_per_category=3):
    """
    Logic: 
    1. Try specific role in dict.
    2. Try job_title in dict.
    3. If not found, use Gemini AI to generate.
    """
    # Normalize input for dictionary lookup
    target = role if role and role in INTERVIEW_QUESTIONS else job_title

    # Step 1 & 2: Local Lookup
    if target in INTERVIEW_QUESTIONS:
        questions = INTERVIEW_QUESTIONS[target]
        return {
            cat: random.sample(q_list, min(max_per_category, len(q_list)))
            for cat, q_list in questions.items()
        }
    
    # Step 3: AI Fallback
    # This makes the app feel "limitless" during your demo
    return generate_questions_with_ai(target)