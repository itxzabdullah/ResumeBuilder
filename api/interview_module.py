# interview_module.py

import random

# -------------------------------
# INTERVIEW QUESTION BANK
# -------------------------------

INTERVIEW_QUESTIONS = {
    "Frontend Web Developer": {
        "technical": [
            "Explain the difference between HTML, CSS, and JavaScript.",
            "How does React improve performance using Virtual DOM?",
            "What are responsive design principles?",
            "Explain CSS Flexbox and Grid.",
            "How do you optimize frontend performance?"
        ],
        "behavioral": [
            "Describe a time you worked with a designer.",
            "How do you handle tight deadlines?",
            "How do you receive and implement feedback?"
        ],
        "situational": [
            "How would you fix a website that loads slowly?",
            "What would you do if a feature works on Chrome but not Firefox?"
        ]
    },

    "Web Developer": {
        "technical": [
            "What is REST API?",
            "Explain client-server architecture.",
            "What is the difference between frontend and backend?"
        ],
        "behavioral": [
            "Describe a challenging project you worked on.",
            "How do you manage multiple tasks?"
        ],
        "situational": [
            "How would you debug a broken web page?"
        ]
    },

    "Social Media Manager": {
        "technical": [
            "How do you measure social media engagement?",
            "What tools do you use for social media analytics?",
            "Explain organic vs paid social media."
        ],
        "behavioral": [
            "How do you handle negative comments?",
            "How do you manage brand voice?"
        ],
        "situational": [
            "How would you increase engagement for a declining page?"
        ]
    },

    "Network Engineer": {
        "technical": [
            "Explain TCP/IP model.",
            "What is the difference between LAN and WAN?",
            "What are common wireless security protocols?",
            "Explain subnetting."
        ],
        "behavioral": [
            "Describe a major network failure you handled.",
            "How do you prioritize issues?"
        ],
        "situational": [
            "How would you troubleshoot slow network speed?"
        ]
    },

    "Quality Control Manager": {
        "technical": [
            "What is ISO 9001?",
            "Explain statistical process control.",
            "How do you handle quality audits?"
        ],
        "behavioral": [
            "How do you deal with production pressure?",
            "Describe a quality issue you resolved."
        ],
        "situational": [
            "What would you do if quality standards are not met?"
        ]
    }
}

# -------------------------------
# GENERIC FALLBACK QUESTIONS
# -------------------------------

GENERIC_QUESTIONS = {
    "technical": [
        "Explain your technical skill set.",
        "What tools and technologies do you use?",
        "How do you stay updated with industry trends?"
    ],
    "behavioral": [
        "Tell me about yourself.",
        "What are your strengths and weaknesses?",
        "Describe a challenge you faced."
    ],
    "situational": [
        "How do you handle pressure at work?",
        "What would you do if you miss a deadline?"
    ]
}

# -------------------------------
# MAIN FUNCTION
# -------------------------------

def get_interview_questions(job_title, role=None, max_per_category=3):
    """
    Returns interview questions based on job title or role.
    """

    key = role if role in INTERVIEW_QUESTIONS else job_title

    if key in INTERVIEW_QUESTIONS:
        questions = INTERVIEW_QUESTIONS[key]
    else:
        questions = GENERIC_QUESTIONS

    return {
        "technical": random.sample(
            questions["technical"], 
            min(max_per_category, len(questions["technical"]))
        ),
        "behavioral": random.sample(
            questions["behavioral"], 
            min(max_per_category, len(questions["behavioral"]))
        ),
        "situational": random.sample(
            questions["situational"], 
            min(max_per_category, len(questions["situational"]))
        )
    }
